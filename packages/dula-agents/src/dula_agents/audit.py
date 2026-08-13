"""Agent audit (docs/13-Agents/AgentLifecycle.md §2, AgentSecurity.md §1.7).

Every consequential moment of a run — proposal, permission decision, approval, tool result,
state change — is emitted to an `Auditor`. The service backs this with structured logs + a
domain event; the in-memory auditor supports dev/CI and trace assertions. No secret/sensitive
tool content is required to flow here — callers pass metadata, not raw payloads.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class AuditEvent:
    run_id: str
    tenant: str
    subject: str
    kind: str  # e.g. "proposed" | "permission" | "approval" | "executed" | "state"
    detail: dict[str, Any] = field(default_factory=dict)


class Auditor(Protocol):
    async def emit(self, event: AuditEvent) -> None: ...


@dataclass
class InMemoryAuditor:
    events: list[AuditEvent] = field(default_factory=list)

    async def emit(self, event: AuditEvent) -> None:
        self.events.append(event)

    def kinds(self) -> list[str]:
        return [e.kind for e in self.events]
