"""E2E + safety + reporting: drive the built-in playbook through the real AgentRuntime.

These tests prove the Phase 08 acceptance criteria: the supervised playbook runs, **pauses for
approval** at the consequential step, executes only after approval, and reports are grounded in
the trace. The safety tests prove a playbook **cannot bypass** the runtime's controls — an
unauthorized user or a rejected approver yields **zero unauthorized actions**.
"""

from __future__ import annotations

from collections.abc import Callable

from dula_agents.approval import AutoApprovalBroker, PendingApprovalBroker
from dula_agents.audit import InMemoryAuditor
from dula_agents.permissions import AllowSetChecker
from dula_agents.runtime import AgentRuntime
from dula_agents.tools import ToolBackends
from dula_agents.types import ApprovalDecision, RunState
from dula_automation.catalog import default_library, resolve_base_agent
from dula_automation.playbook import compile_playbook
from dula_automation.report import generate_report


def _compiled():  # type: ignore[no-untyped-def]
    pb = default_library().get("triage-enrich-ticket")
    assert pb is not None
    return pb, compile_playbook(pb, resolve_base_agent(pb))


async def test_playbook_pauses_for_approval_then_completes(
    backends: ToolBackends,
    full_checker: AllowSetChecker,
    tenant: str,
    runtime_factory: Callable[..., AgentRuntime],
) -> None:
    _pb, agent = _compiled()
    broker = PendingApprovalBroker()
    auditor = InMemoryAuditor()
    runtime = runtime_factory(backends, full_checker, broker, auditor)

    record = await runtime.start(
        agent=agent,
        goal="Investigate the top alert",
        tenant=tenant,
        subject="maya",
        roles=["analyst"],
    )
    # Read steps ran; the consequential ticket step paused the run.
    assert record.state is RunState.AWAITING_APPROVAL
    assert record.pending_step is not None
    assert record.pending_step.tool == "create_ticket"
    # Ticket title/body were bound from the alert (grounded, not fabricated).
    assert "Suspicious outbound beacon" in record.pending_step.args["title"]
    assert record.unauthorized_actions() == []

    resumed = await runtime.resume(
        record,
        agent,
        decision=ApprovalDecision(approved=True, approver="lead"),
        approver="lead",
        approver_roles=["responder"],
        roles=["analyst"],
    )
    assert resumed.state is RunState.COMPLETED
    assert resumed.unauthorized_actions() == []
    # The ticket was actually created via the ticket sink.
    ticket_step = next(s for s in resumed.steps if s.tool == "create_ticket")
    assert ticket_step.result is not None and ticket_step.result.ok


async def test_report_is_grounded_in_the_completed_run(
    backends: ToolBackends,
    full_checker: AllowSetChecker,
    tenant: str,
    runtime_factory: Callable[..., AgentRuntime],
) -> None:
    _pb, agent = _compiled()
    # Auto-approve so we get a completed run to report on.
    runtime = runtime_factory(
        backends, full_checker, AutoApprovalBroker(approve=True, approver="lead")
    )
    record = await runtime.start(
        agent=agent, goal="Investigate HOST-7", tenant=tenant, subject="maya", roles=["analyst"]
    )
    assert record.state is RunState.COMPLETED

    report = generate_report(record)
    md = report.to_markdown()
    kinds = {e.kind for e in report.evidence}
    assert {"alert", "indicator", "log", "ticket"} <= kinds
    # Grounded claims: a ticket really was created and is cited.
    assert any(e.kind == "ticket" for e in report.evidence)
    assert "approved by lead" in report.executive_summary
    assert "TICKET-1" in md
    assert "untrusted evidence" in md


async def test_report_does_not_claim_a_ticket_when_rejected(
    backends: ToolBackends,
    full_checker: AllowSetChecker,
    tenant: str,
    runtime_factory: Callable[..., AgentRuntime],
) -> None:
    _pb, agent = _compiled()
    runtime = runtime_factory(
        backends, full_checker, AutoApprovalBroker(approve=False, approver="lead")
    )
    record = await runtime.start(
        agent=agent, goal="Investigate", tenant=tenant, subject="maya", roles=["analyst"]
    )
    assert record.state is RunState.HALTED
    assert record.unauthorized_actions() == []

    report = generate_report(record)
    assert not any(e.kind == "ticket" for e in report.evidence)
    assert "**rejected** by lead" in report.executive_summary
    assert "TICKET" not in report.to_markdown().replace("Investigation", "")


async def test_playbook_cannot_bypass_missing_user_permission(
    backends: ToolBackends,
    tenant: str,
    runtime_factory: Callable[..., AgentRuntime],
) -> None:
    """A user not authorized for create_ticket: the playbook proposes it, the runtime refuses,
    and no consequential action executes — even though every read step is allowed."""
    _pb, agent = _compiled()
    checker = AllowSetChecker(
        {"tool.list_alerts", "tool.enrich_indicator", "tool.search_logs"}  # no create_ticket
    )
    # Adversarial broker: would approve everything — must not matter, the permission gate is first.
    runtime = runtime_factory(backends, checker, AutoApprovalBroker(approve=True, approver="x"))
    record = await runtime.start(
        agent=agent, goal="Investigate", tenant=tenant, subject="mallory", roles=["viewer"]
    )
    assert record.state is RunState.HALTED
    assert record.unauthorized_actions() == []
    ticket = next((s for s in record.steps if s.tool == "create_ticket"), None)
    assert ticket is not None and ticket.permitted is False
    assert ticket.result is None  # never executed


async def test_playbook_run_is_fully_audited(
    backends: ToolBackends,
    full_checker: AllowSetChecker,
    tenant: str,
    runtime_factory: Callable[..., AgentRuntime],
) -> None:
    _pb, agent = _compiled()
    auditor = InMemoryAuditor()
    runtime = runtime_factory(
        backends, full_checker, AutoApprovalBroker(approve=True, approver="lead"), auditor
    )
    await runtime.start(
        agent=agent, goal="Investigate", tenant=tenant, subject="maya", roles=["analyst"]
    )
    kinds = auditor.kinds()
    # Every consequential moment is on the audit trail.
    assert {"proposed", "permission", "approval", "executed", "state"} <= set(kinds)
