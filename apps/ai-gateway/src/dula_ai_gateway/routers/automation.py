"""Automation endpoints (Phase 08): list playbooks, run one, read its trace, approve, and report.

A playbook run **is** an agent run — compiled into an `AgentDefinition` and executed by the shared
agent runtime — so consequential steps pause at ``awaiting_approval`` until an authorized user
resolves them, exactly like Phase 06. Reports are generated from the (tenant-scoped) run record and
are grounded strictly in the trace. Runs are never returned cross-tenant.
"""

from __future__ import annotations

from typing import Any

from dula_agents.types import ApprovalDecision, RunRecord, RunState
from dula_automation.catalog import resolve_base_agent
from dula_automation.playbook import Playbook, PlaybookError, compile_playbook
from dula_automation.report import generate_report
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from dula_ai_gateway.deps import Automation, Context, require

router = APIRouter(prefix="/api/v1/automation", tags=["automation"])


class RunPlaybookRequest(BaseModel):
    goal: str = Field(default="", max_length=2000)


class StepOut(BaseModel):
    index: int
    thought: str
    tool: str
    side_effect: str
    permitted: bool | None
    approved: bool | None
    #: Display name of whoever decided. Null until a decision is made. Never used for
    #: authorization — that is `roles` on the token.
    approved_by: str | None = None
    executed_ok: bool | None = None


class PendingApprovalOut(BaseModel):
    step: int
    tool: str
    args: dict[str, Any]
    impact: str


class RunOut(BaseModel):
    run_id: str
    playbook: str
    goal: str
    state: str
    result: str | None
    error: str | None
    steps: list[StepOut]
    pending_approval: PendingApprovalOut | None


class PlaybookStepOut(BaseModel):
    id: str
    tool: str
    description: str


class PlaybookOut(BaseModel):
    name: str
    title: str
    description: str
    base_agent: str
    tags: list[str]
    steps: list[PlaybookStepOut]


class EvidenceOut(BaseModel):
    ref: str
    kind: str
    summary: str
    untrusted: bool


class ReportOut(BaseModel):
    run_id: str
    title: str
    state: str
    outcome: str
    executive_summary: str
    technical_detail: str
    evidence: list[EvidenceOut]
    markdown: str


class ApprovalRequestBody(BaseModel):
    approved: bool
    reason: str = Field(default="", max_length=1000)


def _impact(tool: str, args: dict[str, Any]) -> str:
    if tool == "create_ticket":
        return f"Creates an incident ticket: {args.get('title', '')}"
    if tool == "isolate_host":
        return f"Network-isolates host {args.get('host', '')}"
    return f"Executes consequential tool '{tool}'"


def _playbook_out(pb: Playbook) -> PlaybookOut:
    return PlaybookOut(
        name=pb.name,
        title=pb.title,
        description=pb.description,
        base_agent=pb.base_agent,
        tags=list(pb.tags),
        steps=[PlaybookStepOut(id=s.id, tool=s.tool, description=s.description) for s in pb.steps],
    )


def _run_out(record: RunRecord, playbook: str) -> RunOut:
    pending = record.pending_step
    return RunOut(
        run_id=record.run_id,
        playbook=playbook,
        goal=record.goal,
        state=record.state.value,
        result=record.result,
        error=record.error,
        steps=[
            StepOut(
                index=s.index,
                thought=s.thought,
                tool=s.tool,
                side_effect=s.side_effect.value,
                permitted=s.permitted,
                approved=(s.approval.approved if s.approval is not None else None),
                approved_by=(s.approval.approver_label if s.approval is not None else None),
                executed_ok=(s.result.ok if s.result is not None else None),
            )
            for s in record.steps
        ],
        pending_approval=(
            PendingApprovalOut(
                step=pending.index,
                tool=pending.tool,
                args=pending.args,
                impact=_impact(pending.tool, pending.args),
            )
            if pending is not None
            else None
        ),
    )


@router.get(
    "/playbooks",
    response_model=list[PlaybookOut],
    dependencies=[Depends(require("automation.read"))],
)
async def list_playbooks(automation: Automation) -> list[PlaybookOut]:
    return [_playbook_out(pb) for pb in automation.library.all()]


@router.post(
    "/playbooks/{name}/runs",
    response_model=RunOut,
    dependencies=[Depends(require("automation.run"))],
)
async def run_playbook(
    name: str, data: RunPlaybookRequest, ctx: Context, automation: Automation
) -> RunOut:
    playbook = automation.library.get(name)
    if playbook is None:
        available = ", ".join(automation.library.names())
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"unknown playbook '{name}' (available: {available})",
        )
    try:
        agent = compile_playbook(playbook, resolve_base_agent(playbook))
    except PlaybookError as exc:  # pragma: no cover - built-ins are validated at registration
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc
    goal = data.goal.strip() or f"Run playbook '{playbook.title}'"
    record = await automation.runtime.start(
        agent=agent, goal=goal, tenant=ctx.tenant, subject=ctx.subject, roles=list(ctx.roles)
    )
    automation.store.save(record, tuple(ctx.roles))
    return _run_out(record, playbook.name)


def _stored_or_404(automation: Automation, tenant: str, run_id: str) -> Any:
    stored = automation.store.get(tenant, run_id)
    if stored is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
    return stored


@router.get(
    "/runs/{run_id}",
    response_model=RunOut,
    dependencies=[Depends(require("automation.read"))],
)
async def get_run(run_id: str, ctx: Context, automation: Automation) -> RunOut:
    stored = _stored_or_404(automation, ctx.tenant, run_id)
    return _run_out(stored.record, stored.record.agent)


@router.post(
    "/runs/{run_id}/approval",
    response_model=RunOut,
    dependencies=[Depends(require("automation.approve"))],
)
async def approve_run(
    run_id: str, data: ApprovalRequestBody, ctx: Context, automation: Automation
) -> RunOut:
    stored = _stored_or_404(automation, ctx.tenant, run_id)
    if stored.record.state is not RunState.AWAITING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="run is not awaiting approval"
        )
    playbook = automation.library.get(stored.record.agent)
    if playbook is None:  # pragma: no cover - runs are created from library playbooks
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="playbook no longer exists"
        )
    agent = compile_playbook(playbook, resolve_base_agent(playbook))
    record = await automation.runtime.resume(
        stored.record,
        agent,
        decision=ApprovalDecision(
            approved=data.approved,
            approver=ctx.subject,
            reason=data.reason,
            approver_username=ctx.username,
        ),
        approver=ctx.subject,
        approver_roles=list(ctx.roles),
        roles=list(stored.roles),
    )
    automation.store.save(record, stored.roles)
    return _run_out(record, playbook.name)


@router.get(
    "/runs/{run_id}/report",
    response_model=ReportOut,
    dependencies=[Depends(require("reports.read"))],
)
async def get_report(run_id: str, ctx: Context, automation: Automation) -> ReportOut:
    stored = _stored_or_404(automation, ctx.tenant, run_id)
    report = generate_report(stored.record)
    return ReportOut(
        run_id=report.run_id,
        title=report.title,
        state=report.state,
        outcome=report.outcome,
        executive_summary=report.executive_summary,
        technical_detail=report.technical_detail,
        evidence=[
            EvidenceOut(ref=e.ref, kind=e.kind, summary=e.summary, untrusted=e.untrusted)
            for e in report.evidence
        ],
        markdown=report.to_markdown(),
    )
