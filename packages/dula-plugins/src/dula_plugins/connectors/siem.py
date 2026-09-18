"""SIEM search connector (`siem.search`, read).

Adapts a SIEM to a read capability that returns **normalized** log events (ts/host/message/
source) mapped to the internal shape. Two backends: an in-memory fixture so contract tests and
the offline profile run without live calls, and an **OpenSearch** query backend (ADR-0003's
log-analytics store, and the API most SIEMs speak) that goes through the plugin's egress guard.
Output is untrusted evidence either way.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx

from dula_plugins.connector import ConnectorContext, ConnectorResult
from dula_plugins.egress import EgressError
from dula_plugins.http import EgressHttpClient, HttpError, auth_headers
from dula_plugins.manifest import Capability, PluginManifest, SideEffect
from dula_plugins.sdk import BaseConnector

SIEM_PLUGIN_ID = "dula-plugin-dula-siem"
SIEM_SECRET_KEY = "siem.authorization"  # noqa: S105 - the secret's *name*; value is in the provider


class LogBackend(Protocol):
    async def query(
        self, tenant: str, query: str, limit: int, ctx: ConnectorContext
    ) -> list[dict[str, Any]]: ...


@dataclass
class FixtureLogBackend:
    """Offline log backend: tenant-scoped fixture events, naive substring match."""

    events: dict[str, list[dict[str, Any]]] = field(default_factory=dict)

    async def query(
        self, tenant: str, query: str, limit: int, ctx: ConnectorContext
    ) -> list[dict[str, Any]]:
        terms = [t for t in query.lower().split() if t]
        hits = [
            e
            for e in self.events.get(tenant, [])
            if not terms or any(t in str(e).lower() for t in terms)
        ]
        return hits[:limit]


@dataclass
class OpenSearchLogBackend:
    """``_search`` against a per-tenant index pattern (index namespacing per ADR-0006).

    ``base_url`` must point at a host on the plugin's egress allowlist; the guard in ``ctx`` is
    what actually permits the call. The auth header comes from the scoped secret
    ``siem.authorization`` and is never logged.
    """

    base_url: str
    index_pattern: str = "logs-{tenant}-*"
    timestamp_field: str = "@timestamp"
    transport: httpx.AsyncBaseTransport | None = None

    async def query(
        self, tenant: str, query: str, limit: int, ctx: ConnectorContext
    ) -> list[dict[str, Any]]:
        index = self.index_pattern.format(tenant=tenant)
        url = f"{self.base_url.rstrip('/')}/{index}/_search"
        body = {
            "size": limit,
            "query": {"query_string": {"query": query, "default_field": "message"}},
            "sort": [{self.timestamp_field: {"order": "desc", "unmapped_type": "date"}}],
        }
        client = EgressHttpClient(ctx.egress, transport=self.transport or ctx.transport)
        data = await client.post_json(
            url, body, headers=auth_headers(ctx.secrets.get(SIEM_SECRET_KEY))
        )
        hits = data.get("hits", {}).get("hits", []) if isinstance(data, dict) else []
        out: list[dict[str, Any]] = []
        for hit in hits:
            src = hit.get("_source", {}) if isinstance(hit, dict) else {}
            if not isinstance(src, dict):
                continue
            host = src.get("host")
            if isinstance(host, dict):
                host = host.get("name", "")
            out.append(
                {
                    "ts": src.get(self.timestamp_field) or src.get("ts", ""),
                    "host": host or "",
                    "message": src.get("message") or src.get("msg", ""),
                }
            )
        return out


def siem_manifest(egress: list[str] | None = None) -> PluginManifest:
    return PluginManifest(
        id=SIEM_PLUGIN_ID,
        version="0.2.0",
        publisher_key_id="dula-builtin",
        description="First-party SIEM search connector.",
        egress=list(egress or []),
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
        "ts": str(raw.get("ts", "")),
        "host": str(raw.get("host", "")),
        "message": str(raw.get("message") or raw.get("msg", "")),
        "source": "siem",
    }


class SiemSearchConnector(BaseConnector):
    def __init__(self, backend: LogBackend, *, egress: list[str] | None = None) -> None:
        super().__init__(siem_manifest(egress))
        self._backend = backend
        self.register("siem.search", self._search)

    async def _search(self, args: dict[str, Any], ctx: ConnectorContext) -> ConnectorResult:
        query = args.get("query")
        if not isinstance(query, str) or not query.strip():
            return ConnectorResult(ok=False, error="missing 'query'")
        limit = min(int(args.get("limit", 20)), 100)
        try:
            raw = await self._backend.query(ctx.tenant, query, limit, ctx)
        except EgressError as exc:
            return ConnectorResult(ok=False, error=f"egress denied: {exc}")
        except HttpError as exc:
            return ConnectorResult(ok=False, error=f"siem request failed: {exc}")
        events = [_normalize(e) for e in raw]
        return ConnectorResult(ok=True, output={"count": len(events), "events": events})
