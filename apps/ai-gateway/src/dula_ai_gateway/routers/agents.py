"""Agent endpoints (Phase 06): start a run, read its trace, and approve/reject a paused action.

The runtime enforces the security-critical controls (agent ⊆ user permissions, human approval
for consequential actions, limits, audit); these endpoints only carry the caller's identity and
persist the run. Consequential steps pause the run at ``awaiting_approval`` until an authorized
user resolves it. Runs are tenant-scoped in the store (never returned cross-tenant).
"""

from __future__ import annotations

from typing import Any

from dula_agents.agents import AGENTS, get_agent
from dula_agents.types import ApprovalDecision, RunRecord, RunState
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from dula_ai_gateway.deps import Agents, Context, require

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


class StartRunRequest(BaseModel):
    agent: str = Field(default="investigation-assistant", max_length=64)
    goal: str = Field(min_length=1, max_length=2000)


class ApprovalRequestBody(BaseModel):
    approved: bool
    reason: str = Field(default="", max_length=1000)


class StepOut(BaseModel):
    index: int
    thought: str
    tool: str
    side_effect: str
    permitted: bool | None
    permission_reason: str
    approved: bool | None
    #: Display name of whoever decided, so the trace can attribute the decision. Null until a
    #: decision is made. Never used for authorization — that is `roles` on the token.
    approved_by: str | None = None
    executed_ok: bool | None = None


class PendingApprovalOut(BaseModel):
    step: int
    tool: str
    args: dict[str, Any]
    impact: str


class RunOut(BaseModel):
    run_id: str
    agent: str
    goal: str
    state: str
    result: str | None
    error: str | None
    steps: list[StepOut]
    pending_approval: PendingApprovalOut | None


def _impact(tool: str, args: dict[str, Any]) -> str:
    if tool == "create_ticket":
        return f"Creates an incident ticket: {args.get('title', '')}"
    if tool == "isolate_host":
        return f"Network-isolates host {args.get('host', '')}"
    return f"Executes consequential tool '{tool}'"


def _to_out(record: RunRecord) -> RunOut:
    pending = record.pending_step
    return RunOut(
        run_id=record.run_id,
        agent=record.agent,
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
                permission_reason=s.permission_reason,
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


@router.post("/runs", response_model=RunOut, dependencies=[Depends(require("agents.run"))])
async def start_run(data: StartRunRequest, ctx: Context, agents: Agents) -> RunOut:
    agent = get_agent(data.agent)
    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"unknown agent '{data.agent}' (available: {', '.join(AGENTS)})",
        )
    record = await agents.runtime.start(
        agent=agent, goal=data.goal, tenant=ctx.tenant, subject=ctx.subject, roles=list(ctx.roles)
    )
    agents.store.save(record, tuple(ctx.roles))
    return _to_out(record)


@router.get("/runs/{run_id}", response_model=RunOut, dependencies=[Depends(require("agents.read"))])
async def get_run(run_id: str, ctx: Context, agents: Agents) -> RunOut:
    stored = agents.store.get(ctx.tenant, run_id)
    if stored is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
    return _to_out(stored.record)


@router.post(
    "/runs/{run_id}/approval",
    response_model=RunOut,
    dependencies=[Depends(require("agents.approve"))],
)
async def approve_run(
    run_id: str, data: ApprovalRequestBody, ctx: Context, agents: Agents
) -> RunOut:
    stored = agents.store.get(ctx.tenant, run_id)
    if stored is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="run not found")
    if stored.record.state is not RunState.AWAITING_APPROVAL:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="run is not awaiting approval"
        )
    agent = get_agent(stored.record.agent)
    if agent is None:  # pragma: no cover - agent definitions are static
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="agent no longer exists")
    record = await agents.runtime.resume(
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
    agents.store.save(record, stored.roles)
    return _to_out(record)
