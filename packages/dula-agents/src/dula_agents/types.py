"""Core agent value types (docs/13-Agents/AgentLifecycle.md, ToolCalling.md).

Run states, tool contracts, the run trace, and approval records. Kept dependency-light and
serialisable so a run trace is a faithful, replayable audit record (T7/T11 — agent abuse).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class SideEffect(StrEnum):
    """A tool's side-effect class drives approval gating (ToolCalling.md §4)."""

    READ = "read"  # read-only: permissioned but may run without approval
    CONSEQUENTIAL = "consequential"  # writes/containment: require human approval by default


class RunState(StrEnum):
    """Agent run lifecycle (AgentLifecycle.md §1)."""

    CREATED = "created"
    PLANNING = "planning"
    AWAITING_APPROVAL = "awaiting_approval"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    HALTED = "halted"


TERMINAL_STATES = frozenset({RunState.COMPLETED, RunState.FAILED, RunState.HALTED})


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """Declared tool capability (name is ``verb_noun``)."""

    name: str
    description: str
    side_effect: SideEffect
    permission: str  # OPA action string checked per call (e.g. "tool.search_logs")
    cost: int = 1  # relative cost hint, counted against the run's cost budget


@dataclass(frozen=True, slots=True)
class ToolCall:
    tool: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ToolResult:
    """A tool's output. ``untrusted`` is always True — outputs are evidence, never commands."""

    ok: bool
    output: Any = None
    error: str | None = None
    untrusted: bool = True


@dataclass(frozen=True, slots=True)
class ApprovalRequest:
    """Presented to a human for a consequential action (HumanApproval.md §2)."""

    run_id: str
    step: int
    tool: str
    args: dict[str, Any]
    impact: str
    side_effect: SideEffect


@dataclass(frozen=True, slots=True)
class ApprovalDecision:
    """Who approved a consequential step, and on what grounds.

    Two identities are recorded on purpose. ``approver`` is the OIDC ``sub`` — opaque, stable,
    and never reassigned, so it is what the audit trail is anchored to. ``approver_username``
    is a snapshot of the human-readable name at the moment of approval, kept only so reports
    and the UI can say "approved by raj" instead of quoting a UUID at the reader.

    The username is a snapshot rather than a lookup because Keycloak allows a username to be
    reassigned to a different person later; resolving it at read time would silently rewrite
    history.
    """

    approved: bool
    approver: str
    reason: str = ""
    approver_username: str | None = None

    @property
    def approver_label(self) -> str:
        """The name to show a human. Falls back to the subject when no username was captured."""
        return self.approver_username or self.approver


@dataclass(slots=True)
class Step:
    """One recorded step in a run trace: proposal → checks → outcome."""

    index: int
    thought: str
    tool: str
    args: dict[str, Any]
    side_effect: SideEffect
    permitted: bool | None = None
    permission_reason: str = ""
    approval: ApprovalDecision | None = None
    result: ToolResult | None = None


@dataclass(slots=True)
class RunRecord:
    """The full, replayable record of an agent run (AgentLifecycle.md §2)."""

    run_id: str
    agent: str
    goal: str
    tenant: str
    subject: str
    state: RunState = RunState.CREATED
    steps: list[Step] = field(default_factory=list)
    result: str | None = None
    error: str | None = None

    @property
    def pending_step(self) -> Step | None:
        """The step awaiting approval, if the run is paused."""
        if self.state is not RunState.AWAITING_APPROVAL or not self.steps:
            return None
        last = self.steps[-1]
        return last if last.approval is None and last.result is None else None

    def unauthorized_actions(self) -> list[Step]:
        """Steps whose tool executed without passing both permission and (if needed) approval.

        Used by the safety gate: this list must be **empty** for every run.
        """
        bad: list[Step] = []
        for s in self.steps:
            if s.result is None or not s.result.ok:
                continue
            if s.permitted is not True or (
                s.side_effect is SideEffect.CONSEQUENTIAL
                and (s.approval is None or not s.approval.approved)
            ):
                bad.append(s)
        return bad
