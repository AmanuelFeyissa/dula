"""Assemble the plugin/connector subsystem for the AI Gateway (docs/14-Plugins/, Phase 07).

Builds a `PluginHost` with the built-in connectors installed + enabled, an **OPA-backed**
permission checker (so connector calls are authorized by the same policy as everything else), a
logging auditor, and egress **disabled by default** (air-gapped-first). With nothing configured
the SIEM connector serves a shared demo dataset and tickets go to an in-memory sink, so the
connectors are usable out of the box in the offline profile. Configuring a SIEM URL / ticketing
URL / TI feed host swaps in the HTTP backends, whose hosts become the connectors' egress
allowlists; their credentials are handed over as scoped secrets.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from dula_common.opa import OPAClient
from dula_plugins.builtin import BuiltinBackends, build_offline_host
from dula_plugins.connector import ConnectorContext, InMemorySecrets
from dula_plugins.connectors.siem import (
    SIEM_SECRET_KEY,
    FixtureLogBackend,
    LogBackend,
    OpenSearchLogBackend,
)
from dula_plugins.connectors.ti import TI_FEED_HOST, TI_SECRET_KEY
from dula_plugins.connectors.ticketing import (
    TICKETING_SECRET_KEY,
    FixtureTicketBackend,
    HttpTicketBackend,
    TicketBackend,
)
from dula_plugins.host import PluginHost

from dula_ai_gateway.config import Settings

_log = logging.getLogger(__name__)

_DEMO_LOGS: list[dict[str, Any]] = [
    {"ts": "2026-08-13T01:00:00Z", "host": "HOST-7", "msg": "connection to evil.example.com"},
    {"ts": "2026-08-13T01:02:00Z", "host": "HOST-7", "msg": "periodic beacon 60s"},
]


class _DemoLogBackend(FixtureLogBackend):
    """Returns the shared demo events for any tenant (offline demo; not real tenant data)."""

    async def query(
        self, tenant: str, query: str, limit: int, ctx: ConnectorContext
    ) -> list[dict[str, Any]]:
        terms = [t for t in query.lower().split() if t]
        hits = [e for e in _DEMO_LOGS if not terms or any(t in str(e).lower() for t in terms)]
        return hits[:limit]


class OPAConnectorChecker:
    """`PermissionChecker` backed by OPA — fail-closed."""

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


async def _audit(event: dict[str, Any]) -> None:
    _log.info("connector audit", extra=event)


@dataclass
class PluginsSubsystem:
    host: PluginHost
    backends: BuiltinBackends


def _host_of(url: str) -> list[str]:
    host = urlparse(url).hostname
    return [host] if host else []


def backends_from_settings(settings: Settings) -> tuple[BuiltinBackends, InMemorySecrets]:
    """Fixtures unless a real backend is configured; secrets only for what is configured."""
    logs: LogBackend = _DemoLogBackend()
    tickets: TicketBackend = FixtureTicketBackend()
    secrets: dict[str, str] = {}
    siem_egress: list[str] = []
    ticketing_egress: list[str] = []

    if settings.siem_opensearch_url:
        logs = OpenSearchLogBackend(
            base_url=settings.siem_opensearch_url, index_pattern=settings.siem_index_pattern
        )
        siem_egress = _host_of(settings.siem_opensearch_url)
        if settings.siem_authorization:
            secrets[SIEM_SECRET_KEY] = settings.siem_authorization
    if settings.ticketing_create_url:
        tickets = HttpTicketBackend(
            create_url=settings.ticketing_create_url, id_field=settings.ticketing_id_field
        )
        ticketing_egress = _host_of(settings.ticketing_create_url)
        if settings.ticketing_authorization:
            secrets[TICKETING_SECRET_KEY] = settings.ticketing_authorization
    if settings.ti_feed_host and settings.ti_authorization:
        secrets[TI_SECRET_KEY] = settings.ti_authorization

    backends = BuiltinBackends(
        logs=logs,
        tickets=tickets,
        siem_egress=siem_egress,
        ticketing_egress=ticketing_egress,
        ti_feed_host=settings.ti_feed_host or TI_FEED_HOST,
    )
    return backends, InMemorySecrets(secrets)


def build_plugins_subsystem(opa: OPAClient, settings: Settings) -> PluginsSubsystem:
    backends, secrets = backends_from_settings(settings)
    host, backends = build_offline_host(
        OPAConnectorChecker(opa),
        backends=backends,
        secrets=secrets,
        egress_enabled=settings.plugins_egress_enabled,
        audit=_audit,
    )
    _log.info(
        "connectors wired",
        extra={
            "siem": type(backends.logs).__name__,
            "ticketing": type(backends.tickets).__name__,
            "ti_feed_host": backends.ti_feed_host,
            "egress_enabled": settings.plugins_egress_enabled,
        },
    )
    return PluginsSubsystem(host=host, backends=backends)
