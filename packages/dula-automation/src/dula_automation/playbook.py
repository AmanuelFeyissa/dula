"""Declarative playbooks over the agent runtime (Phase 08 — docs/13-Agents/Playbooks.md).

A **playbook** is a declarative, multi-step security procedure (triage → enrich → corroborate →
recommend). It is compiled into a `Planner` and executed by the **existing** `AgentRuntime`, so
every security control still applies unchanged: the tool must be in the agent's allowlist ∩ the
invoking user's authorization, **consequential steps pause for human approval**, run limits bound
autonomy, and every step is audited. **A playbook cannot bypass these controls** — it only decides
*which permitted step to propose next*; the runtime remains the sole executor.

The planner is **stateless**: it reconstructs progress by replaying the declarative steps against
the run history each call, so a single compiled playbook is safe to reuse across many runs and to
resume out-of-band after an approval pause (mirroring `RuleBasedInvestigationPlanner`). Conditions
and value bindings may reference only *earlier* steps, whose results are fixed once executed, which
makes the replay deterministic and offline — reproducible in CI and air-gapped.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from dula_agents.permissions import AgentScope
from dula_agents.planner import PlanStep
from dula_agents.runtime import AgentDefinition
from dula_agents.types import SideEffect, Step


class PlaybookError(ValueError):
    """Raised when a playbook is malformed or references a tool outside the agent's scope."""


# ---- Value bindings (declarative, no eval) ---------------------------------------------


@dataclass(frozen=True, slots=True)
class Ref:
    """Reference a value from a prior step's **untrusted** output by dotted path.

    ``path`` navigates dict keys and list indices (e.g. ``"alerts.0.indicator"``); an empty path
    yields the whole output. Missing/failed steps or unreachable paths resolve to ``default``.
    """

    step: str
    path: str = ""
    default: Any = None


@dataclass(frozen=True, slots=True)
class Template:
    """A string built from literal text with ``{name}`` placeholders filled by resolved refs.

    Missing refs render as empty strings (never raise), keeping report/ticket text grounded in
    whatever the run actually produced.
    """

    text: str
    refs: Mapping[str, Ref] = field(default_factory=dict)


# A step argument is a literal, a Ref (single value), or a Template (formatted string).
Binding = Any


class ConditionKind(StrEnum):
    ALWAYS = "always"
    STEP_OK = "step_ok"  # a named prior step executed successfully
    REF_TRUTHY = "ref_truthy"  # a referenced value is truthy
    REF_NONEMPTY = "ref_nonempty"  # a referenced value is non-empty (len > 0 / truthy)


@dataclass(frozen=True, slots=True)
class Condition:
    """Gate on which a step runs, evaluated against earlier steps only (deterministic)."""

    kind: ConditionKind = ConditionKind.ALWAYS
    step: str | None = None
    ref: Ref | None = None

    @classmethod
    def always(cls) -> Condition:
        return cls(ConditionKind.ALWAYS)

    @classmethod
    def step_ok(cls, step: str) -> Condition:
        return cls(ConditionKind.STEP_OK, step=step)

    @classmethod
    def ref_truthy(cls, ref: Ref) -> Condition:
        return cls(ConditionKind.REF_TRUTHY, ref=ref)

    @classmethod
    def ref_nonempty(cls, ref: Ref) -> Condition:
        return cls(ConditionKind.REF_NONEMPTY, ref=ref)

    def referenced_step(self) -> str | None:
        if self.step is not None:
            return self.step
        return self.ref.step if self.ref is not None else None


@dataclass(frozen=True, slots=True)
class PlaybookStep:
    """One declarative step: a tool call, an optional guard, and optional dynamic args."""

    id: str
    tool: str
    description: str
    args: Mapping[str, Any] = field(default_factory=dict)
    bind: Mapping[str, Binding] = field(default_factory=dict)
    when: Condition = field(default_factory=Condition.always)

    def referenced_steps(self) -> set[str]:
        refs: set[str] = set()
        guard = self.when.referenced_step()
        if guard is not None:
            refs.add(guard)
        for binding in self.bind.values():
            if isinstance(binding, Ref):
                refs.add(binding.step)
            elif isinstance(binding, Template):
                refs.update(r.step for r in binding.refs.values())
        return refs


@dataclass(frozen=True, slots=True)
class Playbook:
    """A named, declarative procedure bound to a base agent (whose scope/limits it inherits)."""

    name: str
    title: str
    description: str
    base_agent: str
    steps: tuple[PlaybookStep, ...]
    tags: tuple[str, ...] = ()


# ---- Resolution (used by the planner and reused by reporting) --------------------------


def _navigate(value: Any, part: str) -> Any:
    if isinstance(value, Mapping):
        return value.get(part)
    if isinstance(value, (list, tuple)):
        if part.lstrip("-").isdigit():
            idx = int(part)
            if -len(value) <= idx < len(value):
                return value[idx]
        return None
    return None


def resolve_ref(ref: Ref, by_id: Mapping[str, Step]) -> Any:
    """Resolve a `Ref` against successfully-executed steps; unreachable → ``ref.default``."""
    step = by_id.get(ref.step)
    if step is None or step.result is None or not step.result.ok:
        return ref.default
    value: Any = step.result.output
    for part in (p for p in ref.path.split(".") if p):
        value = _navigate(value, part)
        if value is None:
            return ref.default
    return value if value is not None else ref.default


def _stringify(value: Any) -> str:
    return "" if value is None else str(value)


class _SafeDict(dict[str, str]):
    def __missing__(self, key: str) -> str:  # pragma: no cover - defensive
        return ""


def _render_template(tpl: Template, by_id: Mapping[str, Step]) -> str:
    values = {name: _stringify(resolve_ref(ref, by_id)) for name, ref in tpl.refs.items()}
    return tpl.text.format_map(_SafeDict(values))


def _resolve_binding(binding: Binding, by_id: Mapping[str, Step]) -> Any:
    if isinstance(binding, Ref):
        return resolve_ref(binding, by_id)
    if isinstance(binding, Template):
        return _render_template(binding, by_id)
    return binding


def _resolve_args(step: PlaybookStep, by_id: Mapping[str, Step]) -> dict[str, Any]:
    args: dict[str, Any] = dict(step.args)
    for name, binding in step.bind.items():
        args[name] = _resolve_binding(binding, by_id)
    return args


def _condition_holds(cond: Condition, by_id: Mapping[str, Step]) -> bool:
    if cond.kind is ConditionKind.ALWAYS:
        return True
    if cond.kind is ConditionKind.STEP_OK:
        step = by_id.get(cond.step or "")
        return step is not None and step.result is not None and step.result.ok
    if cond.ref is None:
        return False
    value = resolve_ref(cond.ref, by_id)
    if cond.kind is ConditionKind.REF_NONEMPTY:
        try:
            return len(value) > 0
        except TypeError:
            return bool(value)
    return bool(value)  # REF_TRUTHY


# ---- Planner + compilation --------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class PlaybookPlanner:
    """Stateless `Planner` that walks a playbook's steps, gated by conditions, binding args from
    prior outputs. Progress is reconstructed from ``history`` each call, so the same instance is
    reused safely across runs and resumes."""

    playbook: Playbook

    async def next_step(self, *, goal: str, history: list[Step]) -> PlanStep:
        by_id: dict[str, Step] = {}
        consumed = 0
        for pstep in self.playbook.steps:
            if not _condition_holds(pstep.when, by_id):
                continue  # skipped: produced no history entry
            if consumed < len(history):
                by_id[pstep.id] = history[consumed]
                consumed += 1
                continue
            return PlanStep(
                thought=pstep.description,
                tool=pstep.tool,
                args=_resolve_args(pstep, by_id),
            )
        return PlanStep(
            thought=f"Playbook '{self.playbook.name}' complete.",
            finish=True,
            result=_trace_summary(self.playbook, history),
        )


def _trace_summary(playbook: Playbook, history: list[Step]) -> str:
    parts = [f"{s.tool}:{'ok' if (s.result and s.result.ok) else 'skipped'}" for s in history]
    return f"Playbook '{playbook.name}' trace — " + "; ".join(parts)


def validate_playbook(playbook: Playbook, base_agent: AgentDefinition) -> None:
    """Fail closed at authoring time: unique ids, in-scope tools, only backward references.

    This is a convenience guardrail; the runtime independently enforces the agent ∩ user scope on
    every call, so a playbook that slips a bad tool through can still never *execute* it.
    """
    if not playbook.steps:
        raise PlaybookError(f"playbook '{playbook.name}' has no steps")
    scope: AgentScope = base_agent.scope
    seen: set[str] = set()
    for pstep in playbook.steps:
        if pstep.id in seen:
            raise PlaybookError(f"duplicate step id '{pstep.id}' in playbook '{playbook.name}'")
        if not scope.permits_tool(pstep.tool):
            raise PlaybookError(
                f"step '{pstep.id}' uses tool '{pstep.tool}' outside agent "
                f"'{base_agent.name}' allowlist"
            )
        for dep in pstep.referenced_steps():
            if dep not in seen:
                raise PlaybookError(
                    f"step '{pstep.id}' references '{dep}' which is not an earlier step"
                )
        seen.add(pstep.id)


def compile_playbook(playbook: Playbook, base_agent: AgentDefinition) -> AgentDefinition:
    """Compile a playbook into an `AgentDefinition` that inherits the base agent's least-privilege
    scope and limits but plans via the playbook. Validated before returning."""
    validate_playbook(playbook, base_agent)
    return AgentDefinition(
        name=playbook.name,
        role=f"Automation playbook: {playbook.title}",
        goal_scope=playbook.description,
        scope=base_agent.scope,
        planner=PlaybookPlanner(playbook),
        limits=base_agent.limits,
    )


def has_consequential_step(playbook: Playbook, registry_side_effect: dict[str, SideEffect]) -> bool:
    """True if any step maps to a consequential tool (i.e. the playbook has an approval gate)."""
    return any(
        registry_side_effect.get(s.tool, SideEffect.READ) is SideEffect.CONSEQUENTIAL
        for s in playbook.steps
    )
