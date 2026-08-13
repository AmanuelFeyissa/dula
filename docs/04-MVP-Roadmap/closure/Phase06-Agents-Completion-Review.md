---
title: Phase Completion Review — Phase 06 (Agents)
document_id: MVP-P06-COMPLETION
status: Reviewed
version: 1.0.0
last_updated: 2026-08-13
owner: Engineering
audience: Project Maintainer, Architect, Developer, Security Engineer, ML Engineer, DevOps/SRE
phase: Phase 06 — Agents
related:
  - ../Phase06-Agents.md
  - ./M006-Agents-Closure.md
  - ../../13-Agents/AgentImplementation.md
  - ../../PROJECT_STATE.md
---

# Phase Completion Review — Phase 06 (Agents)

> Produced per **CLAUDE.md §11.9**. Phase 06 contains one milestone (M006); its
> [closure report](./M006-Agents-Closure.md) holds the detailed §11.6/§11.7 assessment.

## Phase objective
Introduce **safe** AI agents that plan and act with permissioned tools and human approval, and
deliver investigation/timeline assistance (UC-03) as the first agentic use case — only after the
safety controls (permissions, approval, limits, audit) are proven.

## Milestones completed
- **M006 — Agents:** COMPLETE ([M006 closure](./M006-Agents-Closure.md)).

## Features / capability delivered
- **Agent runtime** (`packages/dula-agents`): plan/act loop; the planner proposes and the runtime
  is the sole executor, gating each step on tool allowlist → user OPA authorization (agent ⊆ user)
  → human approval for consequential tools; step/cost/time limits; full audited, replayable trace.
- **Investigation assistant** (UC-03): triage → enrich → corroborate → recommend a ticket
  (approval-gated), read-first and least-privilege.
- **API**: `/api/v1/agents/*` (start, read, approve) with per-action OPA authorization.
- **UI**: an `apps/web` **Agents** page (run + approve/reject).
- **Evaluation**: the scenario completes with a full trace; a **release-blocking safety suite**
  proves zero unauthorized actions under adversarial conditions.

## Architecture delivered
Realises ADR-0008: the **security-critical layer is first-party**, and the runtime interface
abstracts the execution engine so LangGraph or a model-backed planner can back it later without
changing the controls. No new infrastructure or product dependency; reuses OPA authorization
(ADR-0009), tenant isolation (ADR-0006), and the LLM Gateway (ADR-0005). The default planner is
deterministic and offline, keeping the scenario reproducible and air-gapped.

## Security posture
No privilege escalation (agent ⊆ user, checked per call at execution time); human approval for
consequential actions with the approver re-checked for the specific tool; untrusted planner/tool
output; bounded autonomy; full audit; tenant-scoped runs. The release-blocking agent-safety suite
and OPA tests run in CI. Aligns with
[../../10-Security/AgentSecurity.md](../../10-Security/AgentSecurity.md) and the AI threat model
(T7/T8/T11).

## Testing status
`ruff`/`ruff format`/`mypy --strict` clean; **157 pytest pass, 5 skipped** (live-backend only) —
+18 runtime/eval/safety and +10 API tests over Phase 05. OPA policy tests extended for the agent
and tool actions. `apps/web` eslint/`tsc --noEmit`/`next build` clean, including `/agents`.

## Documentation status
Created the [Agent Runtime Implementation](../../13-Agents/AgentImplementation.md) and
[Agents API](../../12-API/AgentsAPI.md) docs; set 13-Agents status to CURRENT; updated the 12-API
README, SUMMARY, Glossary, PROJECT_STATE, PROJECT_CONTEXT, and closure README; links validated.

## User-documentation status
Created the [Investigation Agent User Guide](../../17-User-Documentation/AgentsUserGuide.md) (run
the agent; approve/reject consequential actions; safety guarantees); User-Documentation README
index updated.

## Known limitations / technical debt / deferred
- Tools run on in-memory/demo backends; real SIEM/EDR/ticketing connectors are FUTURE (Phase 07).
- Deterministic planner today; a model-backed planner via the LLM Gateway is FUTURE.
- In-memory run store + approval broker (no durable persistence/notifications yet); `isolate_host`
  is policy-gated but not wired to a real connector; optional LangGraph execution backend deferred.

## Outstanding risks
None blocking. The safety controls are enforced by the runtime independent of the planner, so
introducing a model-backed planner later does not weaken them; the safety suite guards against
regressions. Durability/connector gaps are functionality (not safety) gaps addressed in later phases.

## Next-phase prerequisites
Phase 07 (Integrations) wires real connector-backed tools behind the existing agent tool **ports**
and adds the plugin/connector framework; the agent runtime, permissions, and approval flow are
already in place. Not started; begins on explicit go-ahead.

## Phase status
**Phase 06 — COMPLETE.** Implementation, tests, security validation (release-blocking safety
suite), and technical *and* user documentation are done and verified. Awaiting go-ahead for
Phase 07.
