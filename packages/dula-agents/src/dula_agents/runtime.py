"""Agent runtime — the security-critical plan/act loop (ADR-0008; AgentArchitecture.md §2).

This is the **only** component that executes tools, and it does so only after a step passes,
in order: (1) the agent's tool allowlist, (2) the invoking user's authorization (OPA), and
(3) for consequential tools, explicit human approval. Denials halt the run; limits fail it;
everything is audited. The planner is untrusted — these controls hold no matter what it
proposes (AgentSecurity.md §4). Runs pause at AwaitingApproval and resume out-of-band, so the
runtime is re-entrant and reconstructs its counters from the run record.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

from dula_agents.approval import ApprovalBroker
from dula_agents.audit import AuditEvent, Auditor, InMemoryAuditor
from dula_agents.limits import LimitCounter, RunLimits
from dula_agents.permissions import AgentScope, PermissionChecker, effective_decision
from dula_agents.planner import Planner, PlanStep
from dula_agents.tools import ToolContext, ToolRegistry
from dula_agents.types import (
    ApprovalDecision,
    ApprovalRequest,
    RunRecord,
    RunState,
    SideEffect,
    Step,
    ToolResult,
)


@dataclass(frozen=True, slots=True)
class AgentDefinition:
    """Declarative agent: role, goal scope, tool allowlist/limits, and its planner."""

    name: str
    role: str
    goal_scope: str
    scope: AgentScope
    planner: Planner
    limits: RunLimits = field(default_factory=RunLimits)


def _impact(tool: str, args: dict[str, object]) -> str:
    if tool == "create_ticket":
        return f"Creates an incident ticket: {args.get('title', '')}"
    if tool == "isolate_host":
        return f"Network-isolates host {args.get('host', '')} (disrupts connectivity)"
    return f"Executes consequential tool '{tool}'"


class AgentRuntime:
    def __init__(
        self,
        registry: ToolRegistry,
        checker: PermissionChecker,
        broker: ApprovalBroker,
        *,
        auditor: Auditor | None = None,
        id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._registry = registry
        self._checker = checker
        self._broker = broker
        self._auditor = auditor or InMemoryAuditor()
        self._id = id_factory or (lambda: uuid.uuid4().hex)

    async def start(
        self,
        *,
        agent: AgentDefinition,
        goal: str,
        tenant: str,
        subject: str,
        roles: Sequence[str],
    ) -> RunRecord:
        record = RunRecord(
            run_id=self._id(), agent=agent.name, goal=goal, tenant=tenant, subject=subject
        )
        counter = LimitCounter(agent.limits)
        counter.start()
        await self._emit(record, "state", {"state": RunState.CREATED.value})
        return await self._advance(record, agent, counter, roles)

    async def resume(
        self,
        record: RunRecord,
        agent: AgentDefinition,
        *,
        decision: ApprovalDecision,
        approver: str,
        approver_roles: Sequence[str],
        roles: Sequence[str] | None = None,
    ) -> RunRecord:
        """Apply an approval decision to a paused run, then continue the loop.

        ``approver_roles`` authorize the *approval* (an approver may not approve beyond their own
        permissions); ``roles`` are the original invoker's, used for any *subsequent* steps so the
        agent keeps acting as the invoking user — never escalating to the approver's authority.
        """
        pending = record.pending_step
        if pending is None or record.state is not RunState.AWAITING_APPROVAL:
            return record
        pending.approval = decision
        await self._emit(
            record,
            "approval",
            {
                "step": pending.index,
                "tool": pending.tool,
                "approved": decision.approved,
                "approver": approver,
            },
        )
        if not decision.approved:
            return await self._halt(record, f"action '{pending.tool}' rejected by {approver}")

        # An approver may not approve beyond their own permissions (HumanApproval.md §4);
        # re-check the action's authorization for the approver at execution time.
        spec = self._registry.get(pending.tool)
        if spec is None:
            return await self._halt(record, f"unknown tool '{pending.tool}' on resume")
        approver_ok = await self._checker.check(
            action=spec.spec.permission,
            tenant=record.tenant,
            subject=approver,
            roles=approver_roles,
        )
        if not approver_ok:
            return await self._halt(
                record, f"approver {approver} not authorized for '{spec.spec.permission}'"
            )

        counter = self._reconstruct_counter(record, agent.limits)
        await self._execute(record, pending, counter)
        record.state = RunState.EXECUTING
        continuation_roles = approver_roles if roles is None else roles
        return await self._advance(record, agent, counter, continuation_roles, resumed=True)

    # ---- internals ---------------------------------------------------------------------

    async def _advance(
        self,
        record: RunRecord,
        agent: AgentDefinition,
        counter: LimitCounter,
        roles: Sequence[str],
        *,
        resumed: bool = False,
    ) -> RunRecord:
        record.state = RunState.PLANNING
        while True:
            reason = counter.exceeded()
            if reason is not None:
                return await self._fail(record, reason)

            proposal = await agent.planner.next_step(goal=record.goal, history=record.steps)
            if proposal.finish:
                record.state = RunState.COMPLETED
                record.result = proposal.result or "done"
                await self._emit(record, "state", {"state": RunState.COMPLETED.value})
                return record

            step = self._propose(record, proposal)
            counter.steps += 1
            await self._emit(
                record,
                "proposed",
                {"step": step.index, "tool": step.tool, "side_effect": step.side_effect.value},
            )

            tool = self._registry.get(step.tool)
            if tool is None:
                step.permitted = False
                step.permission_reason = f"unknown tool '{step.tool}'"
                return await self._halt(record, step.permission_reason)

            decision = await effective_decision(
                tool_name=step.tool,
                tool_permission=tool.spec.permission,
                consequential=step.side_effect is SideEffect.CONSEQUENTIAL,
                scope=agent.scope,
                checker=self._checker,
                tenant=record.tenant,
                subject=record.subject,
                roles=roles,
            )
            step.permitted = decision.allowed
            step.permission_reason = decision.reason
            await self._emit(
                record,
                "permission",
                {
                    "step": step.index,
                    "tool": step.tool,
                    "allowed": decision.allowed,
                    "reason": decision.reason,
                },
            )
            if not decision.allowed:
                return await self._halt(record, decision.reason)

            if step.side_effect is SideEffect.CONSEQUENTIAL:
                req = ApprovalRequest(
                    run_id=record.run_id,
                    step=step.index,
                    tool=step.tool,
                    args=step.args,
                    impact=_impact(step.tool, step.args),
                    side_effect=step.side_effect,
                )
                verdict = await self._broker.request(req)
                if verdict is None:
                    record.state = RunState.AWAITING_APPROVAL
                    await self._emit(
                        record,
                        "state",
                        {"state": RunState.AWAITING_APPROVAL.value, "step": step.index},
                    )
                    return record
                step.approval = verdict
                await self._emit(
                    record,
                    "approval",
                    {
                        "step": step.index,
                        "tool": step.tool,
                        "approved": verdict.approved,
                        "approver": verdict.approver,
                    },
                )
                if not verdict.approved:
                    return await self._halt(record, f"action '{step.tool}' rejected")

            record.state = RunState.EXECUTING
            await self._execute(record, step, counter)

    def _propose(self, record: RunRecord, proposal: PlanStep) -> Step:
        step = Step(
            index=len(record.steps),
            thought=proposal.thought,
            tool=proposal.tool or "",
            args=dict(proposal.args),
            side_effect=self._side_effect(proposal.tool),
        )
        record.steps.append(step)
        return step

    def _side_effect(self, tool_name: str | None) -> SideEffect:
        tool = self._registry.get(tool_name or "")
        return tool.spec.side_effect if tool is not None else SideEffect.READ

    async def _execute(self, record: RunRecord, step: Step, counter: LimitCounter) -> None:
        tool = self._registry.get(step.tool)
        if tool is None:
            step.result = ToolResult(ok=False, error=f"unknown tool '{step.tool}'")
            return
        ctx = ToolContext(tenant=record.tenant, subject=record.subject)
        result = await tool.run(step.args, ctx)
        step.result = result
        counter.tool_calls += 1
        counter.cost += tool.spec.cost
        await self._emit(
            record,
            "executed",
            {"step": step.index, "tool": step.tool, "ok": result.ok, "error": result.error},
        )

    def _tool_cost(self, name: str) -> int:
        tool = self._registry.get(name)
        return tool.spec.cost if tool is not None else 0

    def _reconstruct_counter(self, record: RunRecord, limits: RunLimits) -> LimitCounter:
        counter = LimitCounter(limits)
        counter.start()
        counter.steps = len(record.steps)
        executed = [s for s in record.steps if s.result is not None]
        counter.tool_calls = len(executed)
        counter.cost = sum(self._tool_cost(s.tool) for s in executed)
        return counter

    async def _halt(self, record: RunRecord, reason: str) -> RunRecord:
        record.state = RunState.HALTED
        record.error = reason
        await self._emit(record, "state", {"state": RunState.HALTED.value, "reason": reason})
        return record

    async def _fail(self, record: RunRecord, reason: str) -> RunRecord:
        record.state = RunState.FAILED
        record.error = reason
        await self._emit(record, "state", {"state": RunState.FAILED.value, "reason": reason})
        return record

    async def _emit(self, record: RunRecord, kind: str, detail: dict[str, object]) -> None:
        await self._auditor.emit(
            AuditEvent(
                run_id=record.run_id,
                tenant=record.tenant,
                subject=record.subject,
                kind=kind,
                detail=detail,
            )
        )
