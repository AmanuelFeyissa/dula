"""Planners (docs/13-Agents/AgentFramework.md §1).

A planner proposes the next step given the goal and the run history; it **never executes**
anything. The default `RuleBasedInvestigationPlanner` is deterministic and offline, so the
investigation scenario (UC-03) is reproducible in CI and works air-gapped — and, crucially,
the *security* guarantees do not depend on the planner being trustworthy: the runtime enforces
permissions and approval regardless of what the planner proposes (AgentSecurity.md §4). A
model-backed planner (via the LLM Gateway) is a drop-in for the same interface (FUTURE).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from dula_agents.types import Step


@dataclass(frozen=True, slots=True)
class PlanStep:
    """A planner's proposal: either a tool call or a decision to finish."""

    thought: str
    tool: str | None = None
    args: dict[str, Any] = field(default_factory=dict)
    finish: bool = False
    result: str | None = None


class Planner(Protocol):
    async def next_step(self, *, goal: str, history: list[Step]) -> PlanStep: ...


def _succeeded(history: list[Step], tool: str) -> Step | None:
    for step in history:
        if step.tool == tool and step.result is not None and step.result.ok:
            return step
    return None


def _attempted(history: list[Step], tool: str) -> bool:
    return any(s.tool == tool for s in history)


@dataclass
class RuleBasedInvestigationPlanner:
    """Deterministic investigation flow: triage → enrich → corroborate → recommend action.

    Reads prior observations to choose the next tool, then proposes a consequential
    ``create_ticket`` (which the runtime will gate on approval) and finishes with a summary.
    """

    async def next_step(self, *, goal: str, history: list[Step]) -> PlanStep:
        alerts_step = _succeeded(history, "list_alerts")
        if alerts_step is None:
            return PlanStep(
                thought="Review open alerts to anchor the investigation.",
                tool="list_alerts",
                args={"limit": 5},
            )

        alert = _top_alert(alerts_step)
        indicator = _indicator_of(alert)
        host = _host_of(alert)

        if not _attempted(history, "enrich_indicator") and indicator:
            return PlanStep(
                thought=f"Enrich the indicator {indicator} from the top alert.",
                tool="enrich_indicator",
                args={"value": indicator},
            )

        if not _attempted(history, "search_logs") and (host or indicator):
            needle = host or indicator or ""
            return PlanStep(
                thought=f"Corroborate by searching logs for {needle}.",
                tool="search_logs",
                args={"query": needle, "limit": 10},
            )

        if not _attempted(history, "create_ticket"):
            title = f"Investigation: {alert.get('title', 'suspicious activity')}"
            return PlanStep(
                thought="Findings warrant an incident ticket (consequential — needs approval).",
                tool="create_ticket",
                args={"title": title, "body": _summary(history)},
            )

        return PlanStep(thought="Investigation complete.", finish=True, result=_summary(history))


def _top_alert(alerts_step: Step) -> dict[str, Any]:
    output = alerts_step.result.output if alerts_step.result else None
    if isinstance(output, dict):
        alerts = output.get("alerts")
        if isinstance(alerts, list) and alerts and isinstance(alerts[0], dict):
            return alerts[0]
    return {}


def _indicator_of(alert: dict[str, Any]) -> str:
    for key in ("indicator", "ioc", "domain", "ip"):
        value = alert.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _host_of(alert: dict[str, Any]) -> str:
    value = alert.get("host")
    return value if isinstance(value, str) else ""


def _summary(history: list[Step]) -> str:
    parts = [f"{s.tool}: {'ok' if (s.result and s.result.ok) else 'skipped'}" for s in history]
    return "Investigation trace — " + "; ".join(parts)


@dataclass
class ScriptedPlanner:
    """Emits a fixed list of proposals, then finishes. Used to script tests and to model an
    **adversarial/compromised** planner for the safety suite (proposing actions the runtime
    must refuse without permission/approval)."""

    steps: list[PlanStep] = field(default_factory=list)
    result: str = "done"
    _i: int = 0

    async def next_step(self, *, goal: str, history: list[Step]) -> PlanStep:
        if self._i < len(self.steps):
            step = self.steps[self._i]
            self._i += 1
            return step
        return PlanStep(thought="No more scripted steps.", finish=True, result=self.result)
