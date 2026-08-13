"""Tests for the agent ⊆ user permission intersection."""

from __future__ import annotations

from dula_agents.permissions import AgentScope, AllowSetChecker, effective_decision
from dula_agents.types import SideEffect

SCOPE = AgentScope(allowed_tools=frozenset({"search_logs", "create_ticket"}))


async def _decide(tool: str, permission: str, consequential: bool, checker: AllowSetChecker):
    return await effective_decision(
        tool_name=tool,
        tool_permission=permission,
        consequential=consequential,
        scope=SCOPE,
        checker=checker,
        tenant="t1",
        subject="u1",
        roles=["analyst"],
    )


async def test_allowed_when_scope_and_user_agree() -> None:
    checker = AllowSetChecker({"tool.search_logs"})
    d = await _decide("search_logs", "tool.search_logs", False, checker)
    assert d.allowed


async def test_denied_when_tool_not_in_agent_allowlist() -> None:
    d = await _decide("isolate_host", "tool.isolate_host", True, AllowSetChecker(allow_all=True))
    assert not d.allowed and "allowlist" in d.reason


async def test_denied_when_user_not_authorized() -> None:
    d = await _decide("search_logs", "tool.search_logs", False, AllowSetChecker(set()))
    assert not d.allowed and "not authorized" in d.reason


async def test_scope_can_forbid_all_consequential() -> None:
    scope = AgentScope(allowed_tools=frozenset({"create_ticket"}), allow_consequential=False)
    d = await effective_decision(
        tool_name="create_ticket",
        tool_permission="tool.create_ticket",
        consequential=True,
        scope=scope,
        checker=AllowSetChecker(allow_all=True),
        tenant="t1",
        subject="u1",
        roles=["analyst"],
    )
    assert not d.allowed and "consequential" in d.reason


def test_side_effect_enum_values() -> None:
    assert SideEffect.READ == "read" and SideEffect.CONSEQUENTIAL == "consequential"
