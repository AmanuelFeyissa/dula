"""Fixtures for agent-runtime tests: seeded offline backends + permission checkers."""

from __future__ import annotations

from collections.abc import Callable

import pytest
from dula_agents.agents import build_investigation_agent, build_offline_runtime
from dula_agents.permissions import AllowSetChecker, PermissionChecker
from dula_agents.runtime import AgentDefinition, AgentRuntime
from dula_agents.tools import (
    InMemoryAlertSource,
    InMemoryContainmentSink,
    InMemoryLogSource,
    InMemoryTicketSink,
    ToolBackends,
)

TENANT = "t1"

ALL_TOOL_ACTIONS = {
    "tool.list_alerts",
    "tool.enrich_indicator",
    "tool.search_logs",
    "tool.create_ticket",
    "tool.isolate_host",
}


@pytest.fixture
def tenant() -> str:
    return TENANT


@pytest.fixture
def backends() -> ToolBackends:
    return ToolBackends(
        logs=InMemoryLogSource(
            events={
                TENANT: [
                    {"ts": "2026-08-13T01:00:00Z", "host": "HOST-7", "msg": "connect to evil.com"},
                    {"ts": "2026-08-13T01:02:00Z", "host": "HOST-7", "msg": "beacon 60s interval"},
                ]
            }
        ),
        alerts=InMemoryAlertSource(
            alerts={
                TENANT: [
                    {
                        "id": "A-1",
                        "title": "Suspicious outbound beacon",
                        "host": "HOST-7",
                        "indicator": "evil.com",
                    }
                ]
            }
        ),
        tickets=InMemoryTicketSink(),
        containment=InMemoryContainmentSink(),
    )


@pytest.fixture
def agent() -> AgentDefinition:
    return build_investigation_agent()


@pytest.fixture
def full_checker() -> AllowSetChecker:
    """A user authorized for every tool action."""
    return AllowSetChecker(set(ALL_TOOL_ACTIONS))


@pytest.fixture
def checker_factory() -> Callable[..., AllowSetChecker]:
    """Return a factory building a checker authorized for all tool actions except the given ones."""

    def _make(*exclude: str) -> AllowSetChecker:
        return AllowSetChecker(ALL_TOOL_ACTIONS - set(exclude))

    return _make


@pytest.fixture
def runtime_factory() -> Callable[..., AgentRuntime]:
    def _make(
        backends: ToolBackends,
        checker: PermissionChecker,
        broker: object | None = None,
        auditor: object | None = None,
    ) -> AgentRuntime:
        runtime, _registry, _backends = build_offline_runtime(
            checker, backends=backends, broker=broker, auditor=auditor
        )
        return runtime

    return _make
