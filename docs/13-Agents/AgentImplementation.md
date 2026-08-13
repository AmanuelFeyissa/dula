---
title: Agent Runtime Implementation
document_id: AGT-006
status: Draft
version: 0.1.0
last_updated: 2026-08-13
owner: AI / Security
audience: Developer, AI Engineer, Security Engineer
phase: Phase 06 — Agents (M006)
related:
  - ./AgentFramework.md
  - ./AgentLifecycle.md
  - ./ToolCalling.md
  - ./AgentPermissions.md
  - ./HumanApproval.md
  - ../03-Architecture/AgentArchitecture.md
  - ../10-Security/AgentSecurity.md
  - ../12-API/AgentsAPI.md
  - ../17-User-Documentation/AgentsUserGuide.md
  - ../adr/ADR-0008-agent-runtime.md
---

# Agent Runtime Implementation

> **Purpose.** Technical reference for the Phase 06 agent runtime delivered in
> **`packages/dula-agents/`** and exposed by **`apps/ai-gateway`**. Realises the design in the
> other `13-Agents/` docs and [AgentArchitecture.md](../03-Architecture/AgentArchitecture.md).
> **Status: CURRENT** (offline profile). User guide:
> [../17-User-Documentation/AgentsUserGuide.md](../17-User-Documentation/AgentsUserGuide.md).

## Design stance

The runtime owns the **security-critical layer** in first-party code (ADR-0008): a step runs
only after passing, in order, (1) the agent's tool **allowlist**, (2) the invoking user's
**authorization** (OPA), and (3) for consequential tools, explicit **human approval**. The
**planner is untrusted** — these controls hold no matter what it proposes, which is the core
defence against prompt-injection-driven tool abuse (AgentSecurity.md §4). The default planner is
**deterministic and offline**, so the investigation scenario is reproducible in CI and works
air-gapped; a model-backed planner (via the LLM Gateway) is a drop-in for the same interface
(FUTURE). Per ADR-0008 the execution graph may later be backed by **LangGraph** without changing
the security layer — the runtime interface abstracts it.

## Components (`dula_agents`)

| Module | Responsibility |
|--------|----------------|
| `types` | `RunState`, `SideEffect`, `ToolSpec/ToolCall/ToolResult`, `Step`, `RunRecord`, approval records. `RunRecord.unauthorized_actions()` is the safety invariant (must be empty). |
| `tools` | `Tool` protocol + `ToolRegistry`; built-in tools (`search_logs`, `enrich_indicator`, `list_alerts` = read; `create_ticket`, `isolate_host` = consequential). Tools reach the platform via injected **ports** (log/alert sources, ticket/containment sinks) — in-memory offline, real connectors in prod. `enrich_indicator` reuses the Phase 05 intel core. |
| `permissions` | `AgentScope` (tool allowlist), the `PermissionChecker` port, and `effective_decision` = **agent allowlist ∩ user authorization**, fail-closed with a recorded reason. |
| `approval` | `ApprovalBroker` port; `PendingApprovalBroker` (real human flow — pauses the run) and `AutoApprovalBroker` (deterministic, tests only). |
| `limits` | Step/tool-call/cost/wall-time caps (`RunLimits` + `LimitCounter`). |
| `audit` | `Auditor` port + `AuditEvent`; every proposal/permission/approval/execution/state-change is emitted (metadata only). |
| `planner` | `Planner` port + `PlanStep`; `RuleBasedInvestigationPlanner` (UC-03) and `ScriptedPlanner` (tests / adversarial driver). |
| `runtime` | `AgentRuntime` — the only executor. `start()` runs the plan/act loop to a terminal or paused state; `resume()` applies an approval and continues. Re-entrant: counters are reconstructed from the run record. |
| `store` | `RunStore` port + tenant-scoped `InMemoryRunStore` (a run is never returned cross-tenant; retains invoker roles for safe resume). |
| `agents` | Declarative `AgentDefinition` + the built-in **investigation-assistant**; `build_offline_runtime` wiring. |

## Control flow

`start` → PLANNING loop: check limits → planner proposes → resolve tool (unknown ⇒ halt) →
`effective_decision` (deny ⇒ halt) → if consequential, request approval (`None` ⇒ pause at
AWAITING_APPROVAL and return; reject ⇒ halt) → execute → observe → repeat until the planner
finishes (COMPLETED) or a limit trips (FAILED). `resume` records the decision, **re-checks the
approver's** authorization for the specific tool (an approver may not approve beyond their own
permissions), executes the pending step, and continues the loop **as the original user** (never
escalating to the approver). Matches the state machine in
[AgentLifecycle.md](./AgentLifecycle.md).

## The investigation assistant (UC-03)

Read-first: `list_alerts` → `enrich_indicator` → `search_logs` → propose `create_ticket`
(consequential ⇒ approval) → summarise. Its scope is least-privilege — it **cannot** isolate
hosts (`isolate_host` is outside its allowlist; a higher-impact containment action gated to
responders/admins in policy).

## Authorization mapping (OPA)

Tool permissions are OPA actions (`tool.search_logs`, `tool.create_ticket`, …). Read tools and
`agents.run`/`agents.read`/`agents.approve` are available to every operational persona;
`tool.create_ticket` is role-gated (analyst/hunter/engineer/responder) and `tool.isolate_host`
is responder/admin only. `agents.approve` only admits the approval request — whether it *takes
effect* depends on the approver's authorization for the specific tool, re-checked by the runtime
(`deploy/opa/policy/authz.rego`).

## Evaluation & safety gate

`packages/dula-agents/tests/` — the investigation scenario completes with a full audited trace,
and a **release-blocking safety suite** asserts **zero unauthorized actions** under: a
tool-outside-allowlist proposal, a missing user permission, a rejected/unauthorized approver,
and a runaway loop (limits). `apps/ai-gateway/tests/test_agents.py` covers the API incl. authz
denial and tenant isolation. Aligns with
[../15-Testing/AgentEvaluation.md](../15-Testing/AgentEvaluation.md) §4.

## Maturity & limits

- Tools run on **in-memory/demo backends** offline; real SIEM/EDR/ticketing connectors are
  FUTURE (Phase 07) behind the same ports.
- The planner is **deterministic** today; a model-backed planner via the LLM Gateway is FUTURE.
- The run store and approval broker are **in-memory**; durable persistence + notifications are
  FUTURE. Containment (`isolate_host`) is defined and policy-gated but not wired to a real
  connector.
