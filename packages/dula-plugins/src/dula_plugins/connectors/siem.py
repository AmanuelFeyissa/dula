"""SIEM search connector (`siem.search`, read).

Adapts a SIEM to a read capability that returns **normalized** log events (ts/host/message/
source) mapped to the internal shape. Offline it is backed by an in-memory fixture so contract
tests run without live calls; a production build would issue an HTTP query through the egress
guard. Output is untrusted evidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from dula_plugins.connector import ConnectorContext, ConnectorResult
from dula_plugins.manifest import Capability, PluginManifest, SideEffect
from dula_plugins.sdk import BaseConnector

SIEM_PLUGIN_ID = "dula-plugin-dula-siem"


class LogBackend(Protocol):
    async def query(self, tenant: str, query: str, limit: int) -> list[dict[str, Any]]: ...


@dataclass
class FixtureLogBackend:
    """Offline log backend: tenant-scoped fixture events, naive substring match."""

    events: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    async def query(self, tenant: str, query: str, limit: int) -> list[dict[str, Any]]:
        terms = [t for t in query.lower().split() if t]
        hits = [
            e
            for e in self.events.get(tenant, [])
            if not terms or any(t in str(e).lower() for t in terms)
        ]
        return hits[:limit]


def siem_manifest() -> PluginManifest:
    return PluginManifest(
        id=SIEM_PLUGIN_ID,
        version="0.1.0",
        publisher_key_id="dula-builtin",
        description="First-party SIEM search connector.",
        capabilities=[
            Capability(
                name="siem.search",
                side_effect=SideEffect.READ,
                permission="connector.siem.search",
                description="Search SIEM logs for events matching a query.",
            )
        ],
    )


def _normalize(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "ts": raw.get("ts", ""),
        "host": raw.get("host", ""),
        "message": raw.get("message") or raw.get("msg", ""),
        "source": "siem",
    }


class SiemSearchConnector(BaseConnector):
    def __init__(self, backend: LogBackend) -> None:
        super().__init__(siem_manifest())
        self._backend = backend
        self.register("siem.search", self._search)

    async def _search(self, args: dict[str, Any], ctx: ConnectorContext) -> ConnectorResult:
        query = args.get("query")
        if not isinstance(query, str) or not query.strip():
            return ConnectorResult(ok=False, error="missing 'query'")
        limit = min(int(args.get("limit", 20)), 100)
        raw = await self._backend.query(ctx.tenant, query, limit)
        events = [_normalize(e) for e in raw]
        return ConnectorResult(ok=True, output={"count": len(events), "events": events})
