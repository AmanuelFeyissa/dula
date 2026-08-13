"""Built-in plugin bundle + offline host assembly.

Signs the first-party connectors with a built-in publisher key, trusts that key, and installs +
enables them on a `PluginHost` wired to offline fixture backends. This mirrors the real flow
(sign → verify on install → enable) while running fully offline. Egress is **disabled by
default** (air-gapped-first): the egress-gated `ti.live_lookup` is inert until egress is enabled.
"""

from __future__ import annotations

from dataclasses import dataclass

from dula_plugins.connector import InMemorySecrets, SecretProvider
from dula_plugins.connectors.siem import FixtureLogBackend, SiemSearchConnector
from dula_plugins.connectors.ti import ThreatIntelConnector
from dula_plugins.connectors.ticketing import FixtureTicketBackend, TicketingConnector
from dula_plugins.host import AuditHook, PermissionChecker, PluginHost
from dula_plugins.signing import TrustStore, generate_keypair, sign_manifest

BUILTIN_KEY_ID = "dula-builtin"


@dataclass
class BuiltinBackends:
    logs: FixtureLogBackend
    tickets: FixtureTicketBackend


def build_offline_host(
    checker: PermissionChecker,
    *,
    backends: BuiltinBackends | None = None,
    secrets: SecretProvider | None = None,
    egress_enabled: bool = False,
    resolve_egress: bool = True,
    audit: AuditHook | None = None,
) -> tuple[PluginHost, BuiltinBackends]:
    """Assemble a host with the built-in connectors installed + enabled → (host, backends)."""
    if backends is None:
        backends = BuiltinBackends(logs=FixtureLogBackend(), tickets=FixtureTicketBackend())
    private_key, public_bytes = generate_keypair()
    trust = TrustStore()
    trust.trust(BUILTIN_KEY_ID, public_bytes)

    host = PluginHost(
        trust=trust,
        checker=checker,
        secrets=secrets or InMemorySecrets(),
        egress_enabled=egress_enabled,
        resolve_egress=resolve_egress,
        audit=audit,
    )

    connectors = [
        SiemSearchConnector(backends.logs),
        ThreatIntelConnector(),
        TicketingConnector(backends.tickets),
    ]
    for connector in connectors:
        signed = sign_manifest(connector.manifest, private_key)
        host.install(signed, connector)
        host.enable(connector.manifest.id)

    return host, backends
