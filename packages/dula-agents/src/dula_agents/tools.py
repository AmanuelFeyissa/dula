"""Tool calling (docs/13-Agents/ToolCalling.md).

Typed, declared tools with a strict contract: the model only *proposes* a tool + args; the
runtime validates, permission-checks, and (for consequential tools) gates on approval before
the tool's ``run`` is ever called. Tool **outputs are untrusted evidence**.

Tools reach the platform through injected **ports** (log source, alert source, ticket/
containment sinks), so the toolset runs fully offline with in-memory backends in dev/CI and
against real connectors in production without changing the runtime or the security layer.
`enrich_indicator` reuses the Phase 05 deterministic intel core.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from dula_ai.intel.attack import extract_techniques
from dula_ai.intel.iocs import extract

from dula_agents.types import SideEffect, ToolResult, ToolSpec


@dataclass(frozen=True, slots=True)
class ToolContext:
    """Execution context handed to every tool: tenant scope + acting subject."""

    tenant: str
    subject: str


@runtime_checkable
class Tool(Protocol):
    spec: ToolSpec

    async def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult: ...


# ---- Ports (implemented in-memory here; real connectors in production) ------------------


class LogSource(Protocol):
    async def search(self, tenant: str, query: str, limit: int) -> list[dict[str, Any]]: ...


class AlertSource(Protocol):
    async def list_open(self, tenant: str, limit: int) -> list[dict[str, Any]]: ...


class TicketSink(Protocol):
    async def create(self, tenant: str, title: str, body: str) -> str: ...


class ContainmentSink(Protocol):
    async def isolate_host(self, tenant: str, host: str) -> str: ...


@dataclass
class InMemoryLogSource:
    """Offline log source: tenant-scoped fixture events, naive substring match."""

    events: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    async def search(self, tenant: str, query: str, limit: int) -> list[dict[str, Any]]:
        terms = [t for t in query.lower().split() if t]
        hits = [
            e
            for e in self.events.get(tenant, [])
            if not terms or any(t in str(e).lower() for t in terms)
        ]
        return hits[:limit]


@dataclass
class InMemoryAlertSource:
    alerts: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    async def list_open(self, tenant: str, limit: int) -> list[dict[str, Any]]:
        return self.alerts.get(tenant, [])[:limit]


@dataclass
class InMemoryTicketSink:
    created: list[dict[str, str]] = field(default_factory=list)

    async def create(self, tenant: str, title: str, body: str) -> str:
        ticket_id = f"TICKET-{len(self.created) + 1}"
        self.created.append({"id": ticket_id, "tenant": tenant, "title": title, "body": body})
        return ticket_id


@dataclass
class InMemoryContainmentSink:
    isolated: list[dict[str, str]] = field(default_factory=list)

    async def isolate_host(self, tenant: str, host: str) -> str:
        action_id = f"ISOLATE-{len(self.isolated) + 1}"
        self.isolated.append({"id": action_id, "tenant": tenant, "host": host})
        return action_id


# ---- Built-in tools --------------------------------------------------------------------


def _require_str(args: dict[str, Any], key: str) -> str | None:
    value = args.get(key)
    return value if isinstance(value, str) and value.strip() else None


@dataclass
class SearchLogsTool:
    source: LogSource
    spec: ToolSpec = field(
        default_factory=lambda: ToolSpec(
            "search_logs",
            "Search security logs for events matching a query.",
            SideEffect.READ,
            "tool.search_logs",
        )
    )

    async def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        query = _require_str(args, "query")
        if query is None:
            return ToolResult(ok=False, error="missing 'query'")
        limit = int(args.get("limit", 20))
        events = await self.source.search(ctx.tenant, query, min(limit, 100))
        return ToolResult(ok=True, output={"count": len(events), "events": events})


@dataclass
class EnrichIndicatorTool:
    """Deterministic enrichment via the Phase 05 intel core (no network)."""

    spec: ToolSpec = field(
        default_factory=lambda: ToolSpec(
            "enrich_indicator",
            "Extract IOCs and ATT&CK techniques from a string/advisory.",
            SideEffect.READ,
            "tool.enrich_indicator",
        )
    )

    async def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        value = _require_str(args, "value")
        if value is None:
            return ToolResult(ok=False, error="missing 'value'")
        indicators = [
            {"kind": i.kind, "value": i.value, "defanged": i.defanged} for i in extract(value)
        ]
        techniques = [
            {"id": t.id, "name": t.name, "tactic": t.tactic} for t in extract_techniques(value)
        ]
        return ToolResult(ok=True, output={"indicators": indicators, "techniques": techniques})


@dataclass
class ListAlertsTool:
    source: AlertSource
    spec: ToolSpec = field(
        default_factory=lambda: ToolSpec(
            "list_alerts",
            "List the tenant's open alerts.",
            SideEffect.READ,
            "tool.list_alerts",
        )
    )

    async def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        limit = int(args.get("limit", 20))
        alerts = await self.source.list_open(ctx.tenant, min(limit, 100))
        return ToolResult(ok=True, output={"count": len(alerts), "alerts": alerts})


@dataclass
class CreateTicketTool:
    sink: TicketSink
    spec: ToolSpec = field(
        default_factory=lambda: ToolSpec(
            "create_ticket",
            "Create an incident ticket (consequential).",
            SideEffect.CONSEQUENTIAL,
            "tool.create_ticket",
        )
    )

    async def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        title = _require_str(args, "title")
        if title is None:
            return ToolResult(ok=False, error="missing 'title'")
        body = args.get("body", "") if isinstance(args.get("body", ""), str) else ""
        ticket_id = await self.sink.create(ctx.tenant, title, body)
        return ToolResult(ok=True, output={"ticket_id": ticket_id})


@dataclass
class IsolateHostTool:
    sink: ContainmentSink
    spec: ToolSpec = field(
        default_factory=lambda: ToolSpec(
            "isolate_host",
            "Network-isolate a host (consequential containment).",
            SideEffect.CONSEQUENTIAL,
            "tool.isolate_host",
        )
    )

    async def run(self, args: dict[str, Any], ctx: ToolContext) -> ToolResult:
        host = _require_str(args, "host")
        if host is None:
            return ToolResult(ok=False, error="missing 'host'")
        action_id = await self.sink.isolate_host(ctx.tenant, host)
        return ToolResult(ok=True, output={"action_id": action_id, "host": host})


@dataclass
class ToolRegistry:
    """Name → Tool. The runtime resolves tools here; unknown tools are rejected."""

    tools: dict[str, Tool] = field(default_factory=dict)

    def register(self, tool: Tool) -> None:
        self.tools[tool.spec.name] = tool

    def get(self, name: str) -> Tool | None:
        return self.tools.get(name)

    def specs(self) -> list[ToolSpec]:
        return [t.spec for t in self.tools.values()]


@dataclass
class ToolBackends:
    """The injected ports the default toolset runs on (in-memory offline; real in prod)."""

    logs: LogSource
    alerts: AlertSource
    tickets: TicketSink
    containment: ContainmentSink


def in_memory_backends() -> ToolBackends:
    return ToolBackends(
        logs=InMemoryLogSource(),
        alerts=InMemoryAlertSource(),
        tickets=InMemoryTicketSink(),
        containment=InMemoryContainmentSink(),
    )


def default_toolset(backends: ToolBackends) -> ToolRegistry:
    """Wire the standard read + consequential tools onto the given backends."""
    registry = ToolRegistry()
    registry.register(SearchLogsTool(backends.logs))
    registry.register(EnrichIndicatorTool())
    registry.register(ListAlertsTool(backends.alerts))
    registry.register(CreateTicketTool(backends.tickets))
    registry.register(IsolateHostTool(backends.containment))
    return registry
