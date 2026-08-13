"""Assemble the plugin/connector subsystem for the AI Gateway (docs/14-Plugins/, Phase 07).

Builds a `PluginHost` with the built-in connectors installed + enabled, an **OPA-backed**
permission checker (so connector calls are authorized by the same policy as everything else), a
logging auditor, and egress **disabled by default** (air-gapped-first). Seeds the SIEM connector
with a shared demo dataset so the connectors are usable out of the box in the offline profile.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from dula_common.opa import OPAClient
from dula_plugins.builtin import BuiltinBackends, build_offline_host
from dula_plugins.connectors.siem import FixtureLogBackend
from dula_plugins.connectors.ticketing import FixtureTicketBackend
from dula_plugins.host import PluginHost

_log = logging.getLogger(__name__)

_DEMO_LOGS: list[dict[str, Any]] = [
    {"ts": "2026-08-13T01:00:00Z", "host": "HOST-7", "msg": "connection to evil.example.com"},
    {"ts": "2026-08-13T01:02:00Z", "host": "HOST-7", "msg": "periodic beacon 60s"},
]


class _DemoLogBackend(FixtureLogBackend):
    """Returns the shared demo events for any tenant (offline demo; not real tenant data)."""

    async def query(self, tenant: str, query: str, limit: int) -> list[dict[str, Any]]:
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


def build_plugins_subsystem(opa: OPAClient, *, egress_enabled: bool = False) -> PluginsSubsystem:
    backends = BuiltinBackends(logs=_DemoLogBackend(), tickets=FixtureTicketBackend())
    host, backends = build_offline_host(
        OPAConnectorChecker(opa),
        backends=backends,
        egress_enabled=egress_enabled,
        audit=_audit,
    )
    return PluginsSubsystem(host=host, backends=backends)
