"""Built-in agent definitions + offline assembly (docs/13-Agents/AgentFramework.md §4).

The **investigation assistant** (UC-03) triages an alert, enriches its indicators, corroborates
against logs, and recommends an incident ticket — a consequential step that requires human
approval. Its scope is deliberately least-privilege: it can *not* isolate hosts (a higher-impact
containment action lives outside this agent's allowlist). `build_offline_runtime` wires a runtime
on in-memory tools for dev/CI/demo.
"""

from __future__ import annotations

from dula_agents.approval import ApprovalBroker, PendingApprovalBroker
from dula_agents.audit import Auditor
from dula_agents.limits import RunLimits
from dula_agents.permissions import AgentScope, PermissionChecker
from dula_agents.planner import RuleBasedInvestigationPlanner
from dula_agents.runtime import AgentDefinition, AgentRuntime
from dula_agents.tools import ToolBackends, ToolRegistry, default_toolset, in_memory_backends

INVESTIGATION_TOOLS = frozenset({"list_alerts", "enrich_indicator", "search_logs", "create_ticket"})


def build_investigation_agent() -> AgentDefinition:
    """The read-first investigation assistant (UC-03). Consequential ticket gated on approval."""
    return AgentDefinition(
        name="investigation-assistant",
        role="SOC investigation assistant",
        goal_scope="Investigate a security alert using read-only tools; recommend next actions.",
        scope=AgentScope(allowed_tools=INVESTIGATION_TOOLS, allow_consequential=True),
        planner=RuleBasedInvestigationPlanner(),
        limits=RunLimits(),
    )


AGENTS: dict[str, AgentDefinition] = {a.name: a for a in (build_investigation_agent(),)}


def get_agent(name: str) -> AgentDefinition | None:
    return AGENTS.get(name)


def build_offline_runtime(
    checker: PermissionChecker,
    *,
    backends: ToolBackends | None = None,
    broker: ApprovalBroker | None = None,
    auditor: Auditor | None = None,
) -> tuple[AgentRuntime, ToolRegistry, ToolBackends]:
    """Assemble a runtime on in-memory tools. Returns (runtime, registry, backends)."""
    backends = backends or in_memory_backends()
    registry = default_toolset(backends)
    runtime = AgentRuntime(registry, checker, broker or PendingApprovalBroker(), auditor=auditor)
    return runtime, registry, backends
