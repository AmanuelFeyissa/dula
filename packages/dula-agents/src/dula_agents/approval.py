"""Human-in-the-loop approval (docs/13-Agents/HumanApproval.md).

Consequential actions **pause** the run (AwaitingApproval) until an authorized human approves
or rejects; rejection or timeout halts the run. The broker is a port so the service can back it
with a durable queue + notifications; the in-memory implementation supports dev/CI and the
synchronous "auto policy" used to script deterministic evaluation runs.

Approving is itself authorization-gated (an approver may not approve beyond their own
permissions) — the runtime re-checks the action's permission for the approver before resuming.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from dula_agents.types import ApprovalDecision, ApprovalRequest


class ApprovalBroker(Protocol):
    async def request(self, req: ApprovalRequest) -> ApprovalDecision | None:
        """Return a decision, or None if approval is pending (async/human) or timed out."""
        ...


@dataclass
class PendingApprovalBroker:
    """Broker that always defers: every request stays pending until resolved out-of-band.

    Models the real human flow — the run pauses and a separate approve/reject call resolves it.
    """

    requests: list[ApprovalRequest] = field(default_factory=list)

    async def request(self, req: ApprovalRequest) -> ApprovalDecision | None:
        self.requests.append(req)
        return None


@dataclass
class AutoApprovalBroker:
    """Deterministic broker for scenario tests: approve/reject by policy, no human wait.

    ``approve`` decides the outcome; ``approver`` is recorded. Never used in production — the
    default posture is human approval (HumanApproval.md §6: never auto-approve consequential).
    """

    approve: bool = False
    approver: str = "auto-policy"
    reason: str = "scenario policy"
    approver_username: str | None = None

    async def request(self, req: ApprovalRequest) -> ApprovalDecision | None:
        return ApprovalDecision(
            approved=self.approve,
            approver=self.approver,
            reason=self.reason,
            approver_username=self.approver_username,
        )
