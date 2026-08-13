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
from dula_plugins.connector import ConnectorContext, InMemorySecrets
from dula_plugins.connectors.siem import SIEM_PLUGIN_ID
from dula_plugins.connectors.ticketing import TICKETING_PLUGIN_ID
from dula_plugins.egress import EgressGuard, EgressPolicy
from dula_plugins.host import PluginHost

from dula_ai_gateway.plugins_wiring import PluginsSubsystem

_log = logging.getLogger(__name__)

# Connectors invoked as agent tools do not need egress; the agent runtime is the authorization
# boundary for these calls (it already OPA-checked the tool), so we call the connector directly
# through a disabled egress guard.
_INTERNAL_EGRESS = EgressGuard(policy=EgressPolicy(enabled=False), resolve=False)

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


def _connector_ctx(tenant: str) -> ConnectorContext:
    return ConnectorContext(
        tenant=tenant, subject="agent-runtime", egress=_INTERNAL_EGRESS, secrets=InMemorySecrets()
    )


class _ConnectorLogSource:
    """Agent ``LogSource`` backed by the SIEM **connector** (demonstrates agent→connector)."""

    def __init__(self, host: PluginHost) -> None:
        self._host = host

    async def search(self, tenant: str, query: str, limit: int) -> list[dict[str, Any]]:
        connector = self._host.connector(SIEM_PLUGIN_ID)
        if connector is None:
            return []
        result = await connector.invoke(
            "siem.search", {"query": query, "limit": limit}, _connector_ctx(tenant)
        )
        events = result.output.get("events", []) if (result.ok and result.output) else []
        return list(events)


class _ConnectorTicketSink:
    """Agent ``TicketSink`` backed by the ticketing **connector** (approval-gated by runtime)."""

    def __init__(self, host: PluginHost) -> None:
        self._host = host

    async def create(self, tenant: str, title: str, body: str) -> str:
        connector = self._host.connector(TICKETING_PLUGIN_ID)
        if connector is None:
            return "TICKET-ERROR"
        result = await connector.invoke(
            "ticketing.create_ticket", {"title": title, "body": body}, _connector_ctx(tenant)
        )
        return str(result.output["ticket_id"]) if (result.ok and result.output) else "TICKET-ERROR"


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


def build_agent_subsystem(
    opa: OPAClient, plugins: PluginsSubsystem | None = None
) -> AgentSubsystem:
    """Build the agent subsystem. When a plugins subsystem is provided (Phase 07), the agent's
    ``search_logs`` and ``create_ticket`` tools are backed by **connectors** (agent→connector);
    otherwise they use the in-memory demo backends."""
    if plugins is not None:
        logs: Any = _ConnectorLogSource(plugins.host)
        tickets: Any = _ConnectorTicketSink(plugins.host)
    else:
        logs = _DemoLogSource()
        tickets = InMemoryTicketSink()
    backends = ToolBackends(
        logs=logs,
        alerts=_DemoAlertSource(),
        tickets=tickets,
        containment=InMemoryContainmentSink(),
    )
    runtime, _registry, _backends = build_offline_runtime(
        OPAAgentChecker(opa),
        backends=backends,
        broker=PendingApprovalBroker(),
        auditor=LoggingAuditor(),
    )
    return AgentSubsystem(runtime=runtime, store=InMemoryRunStore())
