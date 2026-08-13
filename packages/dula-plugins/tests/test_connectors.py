"""Contract tests for the built-in connectors (offline fixtures, no live calls)."""

from __future__ import annotations

from collections.abc import Callable

from dula_plugins.builtin import BuiltinBackends
from dula_plugins.host import PluginHost

HostFactory = Callable[..., tuple[PluginHost, BuiltinBackends]]


async def test_ti_lookup_scores_known_bad(
    full_checker, backends: BuiltinBackends, host_factory: HostFactory, tenant: str
) -> None:
    host, _ = host_factory(full_checker, backends)
    result = await host.invoke(
        "ti.lookup_indicator",
        {"value": "c2 at evil.com"},
        tenant=tenant,
        subject="u1",
        roles=["analyst"],
    )
    assert result.ok
    reps = {i["value"]: i["reputation"] for i in result.output["indicators"]}
    assert reps.get("evil.com") == "malicious"


async def test_ticketing_is_consequential_and_idempotent(
    full_checker, backends: BuiltinBackends, host_factory: HostFactory, tenant: str
) -> None:
    host, backs = host_factory(full_checker, backends)
    a = await host.invoke(
        "ticketing.create_ticket",
        {"title": "Incident", "body": "b", "idempotency_key": "k1"},
        tenant=tenant,
        subject="u1",
        roles=["responder"],
    )
    b = await host.invoke(
        "ticketing.create_ticket",
        {"title": "Incident", "body": "b", "idempotency_key": "k1"},
        tenant=tenant,
        subject="u1",
        roles=["responder"],
    )
    assert a.output["ticket_id"] == b.output["ticket_id"]  # idempotent
    assert len(backs.tickets.created) == 1


async def test_siem_search_missing_query(
    full_checker, backends: BuiltinBackends, host_factory: HostFactory, tenant: str
) -> None:
    host, _ = host_factory(full_checker, backends)
    result = await host.invoke("siem.search", {}, tenant=tenant, subject="u1", roles=["analyst"])
    assert not result.ok and "query" in (result.error or "")
