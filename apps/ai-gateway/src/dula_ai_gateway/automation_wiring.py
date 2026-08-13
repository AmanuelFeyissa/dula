"""Assemble the automation subsystem for the AI Gateway (docs/13-Agents/Playbooks.md, Phase 08).

Automation **reuses the agent runtime** (the same OPA-backed checker, approval broker, connector-
backed tools, and auditor as Phase 06/07), adding only a `PlaybookLibrary` and a tenant-scoped run
store for playbook runs. Because a playbook is compiled into an `AgentDefinition` and executed by
that same runtime, every control — allowlist ∩ user authorization, human approval for consequential
steps, limits, and audit — holds unchanged; automation adds **no new execution path**.
"""

from __future__ import annotations

from dataclasses import dataclass

from dula_agents.runtime import AgentRuntime
from dula_agents.store import InMemoryRunStore
from dula_automation.catalog import PlaybookLibrary, default_library

from dula_ai_gateway.agents_wiring import AgentSubsystem


@dataclass
class AutomationSubsystem:
    runtime: AgentRuntime
    store: InMemoryRunStore
    library: PlaybookLibrary


def build_automation_subsystem(agents: AgentSubsystem) -> AutomationSubsystem:
    """Build automation on top of the already-wired agent runtime (shared executor + controls)."""
    return AutomationSubsystem(
        runtime=agents.runtime,
        store=InMemoryRunStore(),
        library=default_library(),
    )
