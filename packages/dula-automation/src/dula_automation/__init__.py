"""Dula security automation (Phase 08 — docs/13-Agents/Playbooks.md, ADR-0008).

Composes the Phase 06 agent runtime and Phase 07 connectors into **declarative, approval-gated
playbooks** and **grounded reporting**. A playbook is compiled into a `Planner` and driven by the
**existing** `AgentRuntime`, so all agent controls — allowlist ∩ user authorization, human approval
for consequential steps, run limits, and full audit — hold unchanged. Nothing here can execute a
tool or self-approve; the runtime stays the single executor and the single security boundary.

Everything is deterministic and offline (declarative planner + in-memory backends), so playbook
behaviour is reproducible in CI and works air-gapped.
"""

from __future__ import annotations

from dula_automation.catalog import (
    PlaybookLibrary,
    default_library,
    resolve_base_agent,
)
from dula_automation.playbook import (
    Condition,
    Playbook,
    PlaybookError,
    PlaybookPlanner,
    PlaybookStep,
    Ref,
    Template,
    compile_playbook,
    validate_playbook,
)
from dula_automation.report import Evidence, Report, generate_report

__all__ = [
    "Condition",
    "Evidence",
    "Playbook",
    "PlaybookError",
    "PlaybookLibrary",
    "PlaybookPlanner",
    "PlaybookStep",
    "Ref",
    "Report",
    "Template",
    "compile_playbook",
    "default_library",
    "generate_report",
    "resolve_base_agent",
    "validate_playbook",
]
