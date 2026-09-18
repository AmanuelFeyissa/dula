"""Air-gapped behavior: egress-dependent capabilities are inert; offline ones still work."""

from __future__ import annotations

from collections.abc import Callable

import httpx
from dula_plugins.builtin import BuiltinBackends
from dula_plugins.connector import ConnectorContext, InMemorySecrets
from dula_plugins.connectors.ti import ThreatIntelConnector
from dula_plugins.egress import EgressGuard, EgressPolicy
from dula_plugins.host import PluginHost

HostFactory = Callable[..., tuple[PluginHost, BuiltinBackends]]


async def test_live_lookup_inert_when_air_gapped(
    full_checker, backends: BuiltinBackends, host_factory: HostFactory, tenant: str
) -> None:
    host, _ = host_factory(full_checker, backends, egress_enabled=False)
    result = await host.invoke(
        "ti.live_lookup", {"value": "evil.com"}, tenant=tenant, subject="u1", roles=["analyst"]
    )
    # Inert, not crashing: the capability fails closed with an egress-denied error.
    assert not result.ok and "egress denied" in (result.error or "")


async def test_offline_lookup_works_when_air_gapped(
    full_checker, backends: BuiltinBackends, host_factory: HostFactory, tenant: str
) -> None:
    host, _ = host_factory(full_checker, backends, egress_enabled=False)
    result = await host.invoke(
        "ti.lookup_indicator", {"value": "evil.com"}, tenant=tenant, subject="u1", roles=["analyst"]
    )
    assert result.ok  # offline enrichment needs no egress


async def test_live_lookup_works_when_egress_enabled(tenant: str) -> None:
    # Egress enabled + allowlisted feed host; resolve disabled to avoid live DNS in CI. The feed
    # itself is a mock transport, so the request really goes through the egress-checked client.
    seen: list[httpx.Request] = []

    def feed(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"indicator": "evil.com", "verdict": "malicious"})

    connector = ThreatIntelConnector(
        feed_host="ti.example.com", transport=httpx.MockTransport(feed)
    )
    ctx = ConnectorContext(
        tenant=tenant,
        subject="u1",
        egress=EgressGuard(
            policy=EgressPolicy(allowed_hosts=frozenset({"ti.example.com"}), enabled=True),
            resolve=False,
        ),
        secrets=InMemorySecrets({"ti.authorization": "Bearer feed-token"}),
    )
    result = await connector.invoke("ti.live_lookup", {"value": "evil.com"}, ctx)
    assert result.ok and result.output["live"] is True
    assert result.output["response"]["verdict"] == "malicious"
    assert result.untrusted
    assert seen[0].url.host == "ti.example.com" and seen[0].url.params["indicator"] == "evil.com"
    assert seen[0].headers["authorization"] == "Bearer feed-token"
