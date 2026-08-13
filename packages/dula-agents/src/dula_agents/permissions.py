"""Agent permissions (docs/13-Agents/AgentPermissions.md, ../10-Security/AgentSecurity.md).

Least privilege with **no self-escalation**: effective permission for a tool call is the
**intersection** of (a) the agent definition's tool allowlist and (b) what the invoking user is
authorized to do, checked **per call** at execution time. The model cannot widen this — it only
proposes; the runtime decides. The `PermissionChecker` port is OPA-backed in the service and a
deterministic allow-set in tests.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol


class PermissionChecker(Protocol):
    """Authorization decision for a single agent action (user side of the intersection)."""

    async def check(
        self, *, action: str, tenant: str, subject: str, roles: Sequence[str]
    ) -> bool: ...


@dataclass(frozen=True, slots=True)
class Decision:
    allowed: bool
    reason: str


@dataclass(frozen=True, slots=True)
class AgentScope:
    """The agent side of the intersection: which tools it may use, and its resource limits."""

    allowed_tools: frozenset[str]
    allow_consequential: bool = True  # if False, the agent may never take consequential actions

    def permits_tool(self, tool_name: str) -> bool:
        return tool_name in self.allowed_tools


class AllowSetChecker:
    """Deterministic, offline `PermissionChecker` for tests/dev: a fixed set of allowed actions."""

    def __init__(self, allowed: set[str] | None = None, *, allow_all: bool = False) -> None:
        self._allowed = allowed or set()
        self._allow_all = allow_all

    async def check(self, *, action: str, tenant: str, subject: str, roles: Sequence[str]) -> bool:
        return self._allow_all or action in self._allowed


async def effective_decision(
    *,
    tool_name: str,
    tool_permission: str,
    consequential: bool,
    scope: AgentScope,
    checker: PermissionChecker,
    tenant: str,
    subject: str,
    roles: Sequence[str],
) -> Decision:
    """Compute the effective allow/deny: agent allowlist ∩ user authorization.

    Fails closed at each gate and records a reason for the audit trail. This is the single
    choke point the runtime consults before any tool runs (AgentSecurity.md §1).
    """
    if not scope.permits_tool(tool_name):
        return Decision(False, f"tool '{tool_name}' not in agent allowlist")
    if consequential and not scope.allow_consequential:
        return Decision(False, f"agent scope forbids consequential tool '{tool_name}'")
    user_ok = await checker.check(
        action=tool_permission, tenant=tenant, subject=subject, roles=roles
    )
    if not user_ok:
        return Decision(False, f"user not authorized for '{tool_permission}'")
    return Decision(True, "allowed by agent scope ∩ user authorization")
