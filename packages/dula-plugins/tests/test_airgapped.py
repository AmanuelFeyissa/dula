"""Air-gapped behavior: egress-dependent capabilities are inert; offline ones still work."""

from __future__ import annotations

from collections.abc import Callable

from dula_plugins.builtin import BuiltinBackends
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


async def test_live_lookup_works_when_egress_enabled(
    full_checker, backends: BuiltinBackends, host_factory: HostFactory, tenant: str
) -> None:
    # Egress enabled + allowlisted feed host; resolve disabled to avoid live DNS in CI.
    host, _ = host_factory(full_checker, backends, egress_enabled=True, resolve_egress=False)
    result = await host.invoke(
        "ti.live_lookup", {"value": "evil.com"}, tenant=tenant, subject="u1", roles=["analyst"]
    )
    assert result.ok and result.output["live"] is True
