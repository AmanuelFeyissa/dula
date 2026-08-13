"""Fixtures for plugin-framework tests: permission checkers + seeded offline host."""

from __future__ import annotations

from collections.abc import Callable, Sequence

import pytest
from dula_plugins.builtin import BuiltinBackends, build_offline_host
from dula_plugins.connectors.siem import FixtureLogBackend
from dula_plugins.connectors.ticketing import FixtureTicketBackend
from dula_plugins.host import PluginHost

TENANT = "t1"

ALL_CONNECTOR_ACTIONS = {
    "connector.siem.search",
    "connector.ti.lookup",
    "connector.ti.live_lookup",
    "connector.ticketing.create",
}


class AllowSetChecker:
    def __init__(self, allowed: set[str] | None = None, *, allow_all: bool = False) -> None:
        self._allowed = allowed or set()
        self._allow_all = allow_all

    async def check(self, *, action: str, tenant: str, subject: str, roles: Sequence[str]) -> bool:
        return self._allow_all or action in self._allowed


@pytest.fixture
def tenant() -> str:
    return TENANT


@pytest.fixture
def backends() -> BuiltinBackends:
    return BuiltinBackends(
        logs=FixtureLogBackend(
            events={
                TENANT: [
                    {"ts": "2026-08-13T01:00:00Z", "host": "HOST-7", "msg": "connect to evil.com"},
                    {"ts": "2026-08-13T01:02:00Z", "host": "HOST-7", "msg": "beacon 60s"},
                ]
            }
        ),
        tickets=FixtureTicketBackend(),
    )


@pytest.fixture
def full_checker() -> AllowSetChecker:
    return AllowSetChecker(set(ALL_CONNECTOR_ACTIONS))


@pytest.fixture
def checker_factory() -> Callable[..., AllowSetChecker]:
    def _make(*exclude: str) -> AllowSetChecker:
        return AllowSetChecker(ALL_CONNECTOR_ACTIONS - set(exclude))

    return _make


@pytest.fixture
def host_factory() -> Callable[..., tuple[PluginHost, BuiltinBackends]]:
    def _make(
        checker: AllowSetChecker,
        backends: BuiltinBackends,
        *,
        egress_enabled: bool = False,
        resolve_egress: bool = False,
    ) -> tuple[PluginHost, BuiltinBackends]:
        return build_offline_host(
            checker,
            backends=backends,
            egress_enabled=egress_enabled,
            resolve_egress=resolve_egress,
        )

    return _make
