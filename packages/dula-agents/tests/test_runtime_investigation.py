"""Agent evaluation — the investigation scenario (UC-03) completes correctly and safely."""

from __future__ import annotations

from collections.abc import Callable

from dula_agents.approval import AutoApprovalBroker
from dula_agents.audit import InMemoryAuditor
from dula_agents.runtime import AgentDefinition, AgentRuntime
from dula_agents.tools import ToolBackends
from dula_agents.types import RunState


async def test_investigation_completes_with_full_trace(
    backends: ToolBackends,
    agent: AgentDefinition,
    full_checker,
    tenant: str,
    runtime_factory: Callable[..., AgentRuntime],
) -> None:
    auditor = InMemoryAuditor()
    runtime = runtime_factory(
        backends, full_checker, AutoApprovalBroker(approve=True, approver="responder-1"), auditor
    )
    record = await runtime.start(
        agent=agent,
        goal="Investigate the outbound beacon alert",
        tenant=tenant,
        subject="analyst-1",
        roles=["analyst"],
    )

    assert record.state is RunState.COMPLETED, record.error
    tools_used = [s.tool for s in record.steps]
    # Read-first: triage → enrich → corroborate → recommend a (gated) ticket.
    assert tools_used == ["list_alerts", "enrich_indicator", "search_logs", "create_ticket"]
    # The consequential ticket required — and recorded — approval, then executed.
    ticket_step = record.steps[-1]
    assert ticket_step.approval is not None and ticket_step.approval.approved
    assert ticket_step.result is not None and ticket_step.result.ok
    assert backends.tickets.created  # type: ignore[attr-defined]
    # Safety invariant: nothing ran without passing permission + approval.
    assert record.unauthorized_actions() == []
    # The trace was audited end to end.
    assert "executed" in auditor.kinds() and "approval" in auditor.kinds()


async def test_read_steps_need_no_approval(
    backends: ToolBackends,
    agent: AgentDefinition,
    full_checker,
    tenant: str,
    runtime_factory: Callable[..., AgentRuntime],
) -> None:
    runtime = runtime_factory(backends, full_checker, AutoApprovalBroker(approve=False))
    record = await runtime.start(
        agent=agent,
        goal="Investigate",
        tenant=tenant,
        subject="analyst-1",
        roles=["analyst"],
    )
    # Even with an auto-REJECT broker, the read steps ran (no approval needed); only the
    # consequential ticket was rejected → run halts without a ticket.
    read_steps = [
        s for s in record.steps if s.tool in ("list_alerts", "enrich_indicator", "search_logs")
    ]
    assert all(s.result is not None and s.result.ok for s in read_steps)
    assert record.state is RunState.HALTED
    assert not backends.tickets.created  # type: ignore[attr-defined]
    assert record.unauthorized_actions() == []
