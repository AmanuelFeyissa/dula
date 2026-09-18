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
from dula_agents.types import RunRecord
from dula_automation.catalog import PlaybookLibrary, default_library, resolve_base_agent
from dula_automation.playbook import PlaybookError, compile_playbook
from dula_automation.triggers import InMemoryTriggerStore, Scheduler, TriggerService

from dula_ai_gateway.agents_wiring import AgentSubsystem


@dataclass
class AutomationSubsystem:
    runtime: AgentRuntime
    store: RunStore
    library: PlaybookLibrary
    triggers: TriggerService
    scheduler: Scheduler

    async def start_playbook(
        self, *, playbook: str, goal: str, tenant: str, subject: str, roles: tuple[str, ...]
    ) -> RunRecord:
        """The one way a playbook run starts -- used by the API and by triggers alike."""
        pb = self.library.get(playbook)
        if pb is None:
            raise PlaybookError(f"unknown playbook '{playbook}'")
        agent = compile_playbook(pb, resolve_base_agent(pb))
        record = await self.runtime.start(
            agent=agent, goal=goal, tenant=tenant, subject=subject, roles=list(roles)
        )
        await self.store.save(record, roles)
        return record


def build_automation_subsystem(
    agents: AgentSubsystem, *, store: RunStore | None = None, scheduler_tick_seconds: float = 15.0
) -> AutomationSubsystem:
    """Build automation on top of the already-wired agent runtime (shared executor + controls).

    ``store`` defaults to ``InMemoryRunStore`` (ADR-0016), a *separate* instance from the agent
    subsystem's own store — playbook runs and agent runs stay in distinct pools even when both
    are durable (see ``kind`` on ``PostgresRunStore``). Triggers are in-memory (a durable
    trigger store is FUTURE); the scheduler task is started/stopped by the app lifespan."""
    subsystem = AutomationSubsystem.__new__(AutomationSubsystem)
    subsystem.runtime = agents.runtime
    subsystem.store = store if store is not None else InMemoryRunStore()
    subsystem.library = default_library()
    subsystem.triggers = TriggerService(InMemoryTriggerStore(), subsystem)
    subsystem.scheduler = Scheduler(subsystem.triggers, tick_seconds=scheduler_tick_seconds)
    return subsystem
