"""Assemble the agent subsystem for the AI Gateway (docs/13-Agents/, ADR-0008).

Wires the first-party `AgentRuntime` with an **OPA-backed** permission checker (so agent tool
calls are authorized by the same policy as the rest of the platform), a logging auditor, an
in-memory pending-approval broker + run store, and the offline demo toolset. Consequential
tools pause for human approval; nothing here can self-escalate.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from dula_agents.agents import build_offline_runtime
from dula_agents.approval import PendingApprovalBroker
from dula_agents.audit import AuditEvent, Auditor
from dula_agents.runtime import AgentRuntime
from dula_agents.store import InMemoryRunStore
from dula_agents.tools import (
    InMemoryAlertSource,
    InMemoryContainmentSink,
    InMemoryLogSource,
    InMemoryTicketSink,
    ToolBackends,
)
from dula_common.opa import OPAClient

_log = logging.getLogger(__name__)

# A shared demo alert + logs so the investigation agent is usable out of the box in the offline
# profile (analogous to the seeded public RAG corpus). Not real tenant data.
_DEMO_ALERT: dict[str, Any] = {
    "id": "A-DEMO-1",
    "title": "Suspicious outbound beacon",
    "host": "HOST-7",
    "indicator": "evil.example.com",
}
_DEMO_LOGS: list[dict[str, Any]] = [
    {"ts": "2026-08-13T01:00:00Z", "host": "HOST-7", "msg": "connection to evil.example.com"},
    {"ts": "2026-08-13T01:02:00Z", "host": "HOST-7", "msg": "periodic beacon 60s"},
]


class _DemoAlertSource(InMemoryAlertSource):
    async def list_open(self, tenant: str, limit: int) -> list[dict[str, Any]]:
        return [dict(_DEMO_ALERT)][:limit]


class _DemoLogSource(InMemoryLogSource):
    async def search(self, tenant: str, query: str, limit: int) -> list[dict[str, Any]]:
        terms = [t for t in query.lower().split() if t]
        hits = [e for e in _DEMO_LOGS if not terms or any(t in str(e).lower() for t in terms)]
        return hits[:limit]


class OPAAgentChecker:
    """`PermissionChecker` backed by OPA — fail-closed like the rest of authorization."""

    def __init__(self, opa: OPAClient) -> None:
        self._opa = opa

    async def check(self, *, action: str, tenant: str, subject: str, roles: Sequence[str]) -> bool:
        return await self._opa.allow(
            {
                "subject": {"roles": list(roles), "tenant_id": tenant},
                "action": action,
                "resource": {"tenant_id": tenant},
            }
        )


class LoggingAuditor(Auditor):
    """Structured-log auditor for the agent trace (metadata only — no sensitive payloads)."""

    async def emit(self, event: AuditEvent) -> None:
        _log.info(
            "agent audit",
            extra={
                "run_id": event.run_id,
                "tenant": event.tenant,
                "subject": event.subject,
                "kind": event.kind,
                "detail": event.detail,
            },
        )


@dataclass
class AgentSubsystem:
    runtime: AgentRuntime
    store: InMemoryRunStore


def build_agent_subsystem(opa: OPAClient) -> AgentSubsystem:
    backends = ToolBackends(
        logs=_DemoLogSource(),
        alerts=_DemoAlertSource(),
        tickets=InMemoryTicketSink(),
        containment=InMemoryContainmentSink(),
    )
    runtime, _registry, _backends = build_offline_runtime(
        OPAAgentChecker(opa),
        backends=backends,
        broker=PendingApprovalBroker(),
        auditor=LoggingAuditor(),
    )
    return AgentSubsystem(runtime=runtime, store=InMemoryRunStore())
