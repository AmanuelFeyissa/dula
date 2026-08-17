"""Durable ``RunStore`` backed by Postgres (ADR-0016).

Satisfies the same async ``dula_agents.store.RunStore`` protocol as ``InMemoryRunStore``, so
wiring can swap one for the other without touching the routers. Each call opens its own short
-lived session (there is no per-request DB dependency in the AI Gateway today) and sets the
``app.current_tenant`` GUC for the RLS policy created in ``alembic/versions/0001_agent_runs.py``
— the same defence-in-depth pattern as ``dula_platform_api.db.get_tenant_session``: RLS plus an
explicit ``tenant_id`` filter in the query, so a bypassed or misconfigured policy still fails
closed at the application layer.

A full run is replaced on every ``save()`` (upsert the run row, delete + reinsert its steps)
rather than diffed incrementally — traces are small (a handful of steps) and this keeps the
write trivially correct: whatever ``RunRecord`` the runtime hands back is exactly what gets
persisted, with no partial-update logic to get wrong.
"""

from __future__ import annotations

import uuid

from dula_agents.store import StoredRun
from dula_agents.types import ApprovalDecision, RunRecord, RunState, SideEffect, Step, ToolResult
from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from dula_ai_gateway.models import AgentRun, AgentRunStep


async def _set_tenant(session: AsyncSession, tenant_id: uuid.UUID) -> None:
    await session.execute(
        text("SELECT set_config('app.current_tenant', :tid, false)"), {"tid": str(tenant_id)}
    )


def _to_step(row: AgentRunStep) -> Step:
    approval = None
    if row.approved is not None:
        approval = ApprovalDecision(
            approved=row.approved,
            approver=row.approver or "",
            reason=row.approval_reason,
            approver_username=row.approver_username,
        )
    result = None
    if row.result_ok is not None:
        result = ToolResult(ok=row.result_ok, output=row.result_output, error=row.result_error)
    return Step(
        index=row.step_index,
        thought=row.thought,
        tool=row.tool,
        args=dict(row.args or {}),
        side_effect=SideEffect(row.side_effect),
        permitted=row.permitted,
        permission_reason=row.permission_reason,
        approval=approval,
        result=result,
    )


class PostgresRunStore:
    """One store per subsystem — ``kind`` keeps agent runs and playbook runs in separate pools
    within the shared ``agent_runs``/``agent_run_steps`` tables, matching today's separate
    in-memory stores (``agents_wiring.py`` and ``automation_wiring.py`` each build their own)."""

    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession], *, kind: str) -> None:
        self._sessionmaker = sessionmaker
        self._kind = kind

    async def save(self, record: RunRecord, roles: tuple[str, ...]) -> None:
        run_id = uuid.UUID(hex=record.run_id)
        tenant_id = uuid.UUID(record.tenant)
        async with self._sessionmaker() as session:
            await _set_tenant(session, tenant_id)
            existing = await session.get(AgentRun, run_id)
            if existing is None:
                session.add(
                    AgentRun(
                        id=run_id,
                        tenant_id=tenant_id,
                        kind=self._kind,
                        agent=record.agent,
                        goal=record.goal,
                        subject=record.subject,
                        roles=list(roles),
                        state=record.state.value,
                        result=record.result,
                        error=record.error,
                    )
                )
            else:
                existing.tenant_id = tenant_id
                existing.kind = self._kind
                existing.agent = record.agent
                existing.goal = record.goal
                existing.subject = record.subject
                existing.roles = list(roles)
                existing.state = record.state.value
                existing.result = record.result
                existing.error = record.error
            # Flush the run row first: agent_run_steps FKs to it, and the two are not linked
            # by an ORM relationship() that would let SQLAlchemy order the inserts itself.
            await session.flush()

            await session.execute(delete(AgentRunStep).where(AgentRunStep.run_id == run_id))
            for step in record.steps:
                session.add(
                    AgentRunStep(
                        run_id=run_id,
                        tenant_id=tenant_id,
                        step_index=step.index,
                        thought=step.thought,
                        tool=step.tool,
                        args=dict(step.args),
                        side_effect=step.side_effect.value,
                        permitted=step.permitted,
                        permission_reason=step.permission_reason,
                        approved=(step.approval.approved if step.approval is not None else None),
                        approver=(step.approval.approver if step.approval is not None else None),
                        approver_username=(
                            step.approval.approver_username if step.approval is not None else None
                        ),
                        approval_reason=(step.approval.reason if step.approval is not None else ""),
                        result_ok=(step.result.ok if step.result is not None else None),
                        result_output=(step.result.output if step.result is not None else None),
                        result_error=(step.result.error if step.result is not None else None),
                    )
                )
            await session.commit()

    async def get(self, tenant: str, run_id: str) -> StoredRun | None:
        try:
            run_uuid = uuid.UUID(hex=run_id)
        except ValueError:
            # run_id arrives from the URL path (attacker-controlled) — malformed input is a
            # 404, not a crash.
            return None
        tenant_id = uuid.UUID(tenant)

        async with self._sessionmaker() as session:
            await _set_tenant(session, tenant_id)
            run_row = (
                await session.execute(
                    select(AgentRun).where(
                        AgentRun.id == run_uuid,
                        AgentRun.tenant_id == tenant_id,
                        AgentRun.kind == self._kind,
                    )
                )
            ).scalar_one_or_none()
            if run_row is None:
                return None
            step_rows = (
                (
                    await session.execute(
                        select(AgentRunStep)
                        .where(AgentRunStep.run_id == run_uuid)
                        .order_by(AgentRunStep.step_index)
                    )
                )
                .scalars()
                .all()
            )

        record = RunRecord(
            run_id=run_row.id.hex,
            agent=run_row.agent,
            goal=run_row.goal,
            tenant=str(run_row.tenant_id),
            subject=run_row.subject,
            state=RunState(run_row.state),
            result=run_row.result,
            error=run_row.error,
            steps=[_to_step(s) for s in step_rows],
        )
        return StoredRun(record=record, roles=tuple(run_row.roles))
