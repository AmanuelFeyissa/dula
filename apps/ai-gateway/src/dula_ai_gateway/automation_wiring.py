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
from dula_agents.store import InMemoryRunStore, RunStore
from dula_automation.catalog import PlaybookLibrary, default_library

from dula_ai_gateway.agents_wiring import AgentSubsystem


@dataclass
class AutomationSubsystem:
    runtime: AgentRuntime
    store: RunStore
    library: PlaybookLibrary


def build_automation_subsystem(
    agents: AgentSubsystem, *, store: RunStore | None = None
) -> AutomationSubsystem:
    """Build automation on top of the already-wired agent runtime (shared executor + controls).

    ``store`` defaults to ``InMemoryRunStore`` (ADR-0016), a *separate* instance from the agent
    subsystem's own store — playbook runs and agent runs stay in distinct pools even when both
    are durable (see ``kind`` on ``PostgresRunStore``)."""
    return AutomationSubsystem(
        runtime=agents.runtime,
        store=store if store is not None else InMemoryRunStore(),
        library=default_library(),
    )
