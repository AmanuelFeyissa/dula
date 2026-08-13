---
title: Milestone Closure — M006 (Phase 06 Agents) — Complete
document_id: MVP-M006-CLOSURE
status: Reviewed
version: 1.0.0
last_updated: 2026-08-13
owner: Engineering
audience: Project Maintainer, Developer, Architect, Security Engineer, ML Engineer, DevOps/SRE
phase: Phase 06 — Agents (M006)
related:
  - ../Phase06-Agents.md
  - ../../13-Agents/AgentImplementation.md
  - ../../12-API/AgentsAPI.md
  - ../../17-User-Documentation/AgentsUserGuide.md
  - ../../10-Security/AgentSecurity.md
  - ../../PROJECT_STATE.md
  - ./README.md
---

# Milestone Closure — M006 (Phase 06 Agents)

> Produced per **CLAUDE.md §11.8**. **This milestone is COMPLETE.** The agent runtime, the
> investigation assistant (UC-03), the permission/approval/limit/audit controls, the agents API
> and UI are delivered; the release-blocking agent-safety suite passes (zero unauthorized
> actions); technical + user documentation are complete.

- **Milestone identifier:** M006
- **Milestone name:** Phase 06 — Agents
- **Objective:** Deliver a safe agent runtime (tool calling, permissions, human approval, audit)
  and the investigation/timeline-assist use case (UC-03), per
  [../Phase06-Agents.md](../Phase06-Agents.md) and ADR-0008.

## Implemented functionality
- **Agent runtime** (`packages/dula-agents`): the plan/act loop where the planner **proposes**
  and the runtime is the **sole executor**, running a step only after it passes the agent tool
  **allowlist** → invoking-user **OPA authorization** (agent ⊆ user) → **human approval** for
  consequential tools; with step/tool-call/cost/wall-time **limits** and a full **audited**,
  replayable run trace. Lifecycle: planning → awaiting_approval → executing → completed/failed/
  halted; runs pause and **resume** out-of-band (re-entrant, counters rebuilt from the record).
- **Investigation assistant** (UC-03): deterministic offline planner
  (list_alerts → enrich_indicator → search_logs → recommend create_ticket), least-privilege
  (cannot isolate hosts). `enrich_indicator` reuses the Phase 05 intel core.
- **Tools + ports**: read tools (`search_logs`, `enrich_indicator`, `list_alerts`) and
  consequential tools (`create_ticket`, `isolate_host`) over injected backends (in-memory
  offline; real connectors FUTURE). **Approval broker**, **run store** (tenant-scoped), **auditor**.
- **API** (`apps/ai-gateway`): `POST /api/v1/agents/runs`, `GET .../{run_id}`,
  `POST .../{run_id}/approval`, per-action OPA authorization.
- **UI** (`apps/web`): an **Agents** page (start investigation, view trace, approve/reject),
  nav-linked, over server-proxied routes.

## Technical changes
- New workspace package `packages/dula-agents` (torch-free, offline): `types`, `tools`,
  `permissions`, `approval`, `limits`, `audit`, `planner`, `runtime`, `store`, `agents`.
- `apps/ai-gateway`: new `routers/agents.py` (+ registration in `main.py`), `agents_wiring.py`
  (OPA-backed checker, logging auditor, demo backends, subsystem builder), `deps.py` accessor;
  added `dula-agents` dependency.
- `apps/web`: new `app/agents/page.tsx` + `components/AgentConsole.tsx` + three
  `app/api/agents/runs/**` proxy routes; `Nav.tsx` **Agents** link.
- Root `pyproject.toml`: `dula-agents` workspace member + source.

## Architecture changes
- No new infrastructure. Realises ADR-0008: **build the security-critical layer first-party**;
  the runtime interface abstracts the execution engine so **LangGraph** (or a model-backed
  planner via the LLM Gateway) can back it later without changing the controls. Reuses the
  tenant/authorization model (ADR-0006/0009) and the LLM Gateway (ADR-0005). No new product
  dependency (agent runtime is dependency-light; air-gapped guarantee preserved).

## Database changes
- None. Runs are held in an in-memory, tenant-scoped store (durable persistence FUTURE).

## API changes
- Added three `/api/v1/agents/*` endpoints ([../../12-API/AgentsAPI.md](../../12-API/AgentsAPI.md)).
  New OPA actions: `agents.run`, `agents.read`, `agents.approve`, and per-tool `tool.search_logs`,
  `tool.enrich_indicator`, `tool.list_alerts`, `tool.create_ticket`, `tool.isolate_host` (read
  tools + agent actions to operational personas; `tool.create_ticket` role-gated;
  `tool.isolate_host` responder/admin only).

## Security changes / validation performed
- **No privilege escalation** (agent ⊆ user), enforced **per call** at execution time via OPA.
- **Human approval** required for consequential actions; the approver is re-checked for the
  specific tool's authorization (an approver may not approve beyond their own permissions);
  continuation runs as the **original user**, not the approver.
- **Untrusted planner/tool output**: the controls hold no matter what the planner proposes
  (defence against injection-driven tool abuse); tool outputs are marked untrusted.
- **Limits** bound autonomy; **full audit** of every proposal/decision/execution/state change.
- **Release-blocking safety suite** asserts **zero unauthorized actions** under: tool-outside-
  allowlist proposals, missing user permission, rejected/unauthorized approver, runaway loop.
- API tests cover authz denial (403) and **tenant isolation** (a run is never returned
  cross-tenant). OPA policy tests extended for the new actions.

## AI/ML changes
- The default planner is deterministic (no model). Optional model-backed planning via the LLM
  Gateway is FUTURE and slots into the same `Planner` interface with no runtime/security change.

## Testing performed
- `ruff` + `ruff format --check` clean; `mypy --strict` clean; **157 pytest pass, 5 skipped**
  (live-backend only), up from 129 — **+18** runtime/eval/safety unit tests and **+10** API
  integration tests. OPA policy extended (`opa test` in CI).
- `apps/web`: eslint clean, `tsc --noEmit` clean, `next build` succeeds with `/agents` and the
  three `/api/agents/*` routes.

## Deployment validation
- No new services/infrastructure; endpoints run in the existing `apps/ai-gateway` (offline
  profile verified via the test app). K8s/live-backend deployment unchanged from Phase 03.

## Documentation completed

### Documentation Impact Assessment (CLAUDE.md §11.6)
1. **Implemented:** agent runtime + investigation assistant + `/api/v1/agents/*` + Agents UI.
2. **Technical docs created:** [../../13-Agents/AgentImplementation.md](../../13-Agents/AgentImplementation.md), [../../12-API/AgentsAPI.md](../../12-API/AgentsAPI.md); this closure; Phase 06 Completion Review.
3. **Technical docs updated:** 13-Agents README (status→CURRENT), 12-API README, SUMMARY, Glossary, PROJECT_STATE, PROJECT_CONTEXT, closure README.
4. **User docs created:** [../../17-User-Documentation/AgentsUserGuide.md](../../17-User-Documentation/AgentsUserGuide.md).
5. **User docs updated:** User-Documentation README index.
6. **Intentionally not created (N/A):** Database/Migration (no schema), Model card (no training), DR/Backup (in-memory/stateless MVP), Plugin/connector (real backends are Phase 07).
7. **Examples/commands verified:** endpoint request/response shapes exercised by integration tests.
8. **Links valid:** relative-link check passes. 9. **Diagrams:** existing design diagrams (AgentArchitecture/Lifecycle) remain accurate; none added. 10-11. **Incomplete/gaps:** none blocking; real connectors, durable store, and model-backed planner are FUTURE, not M006 gaps.

### Milestone Documentation Checklist (CLAUDE.md §11.7)
#### Technical
- [x] Architecture updated (implementation doc) · [x] API documentation updated · [N/A] Database
- [x] Configuration (OPA actions) · [x] Security documentation referenced/consistent · [N/A] Deployment (no change)
- [x] Testing documentation updated · [~] Troubleshooting (user-guide "Good to know")
- [N/A] Operational/Runbook (stateless MVP) · [x] Agent documentation updated · [N/A] RAG/Plugin
#### User
- [x] Getting Started / Feature docs (Investigation Agent User Guide) · [x] User guide updated
- [N/A] Admin/Operator guides (no operational surface yet) · [x] Troubleshooting notes · [N/A] FAQ
#### Quality
- [x] Front matter · [x] Naming conventions · [x] Relative links validated
- [x] Commands/examples verified · [x] No undocumented functionality · [x] No FUTURE-as-CURRENT
- [x] SUMMARY updated · [x] Glossary terms added · [x] PROJECT_CONTEXT/STATE updated

## Known limitations
- Tools run on **in-memory/demo backends**; real SIEM/EDR/ticketing connectors are FUTURE (Phase 07).
- The planner is **deterministic**; a model-backed planner via the LLM Gateway is FUTURE.
- The run store + approval broker are **in-memory** (no durable persistence/notifications yet).
- `isolate_host` is defined and policy-gated but not wired to a real containment connector.

## Known issues
- None outstanding.

## Deferred work
- Real connector-backed tools (Phase 07); durable run store + approval notifications;
  model-backed planner behind the LLM Gateway; optional LangGraph execution backend; richer
  agent scenarios (hunt, IR) and a broader agent-evaluation scenario suite.

## Lessons learned
- Making the **runtime** (not the planner) the security boundary yields guarantees that survive
  an untrusted/compromised planner — the safety suite proves *zero unauthorized actions*
  regardless of what is proposed. A deterministic offline planner kept the scenario reproducible
  and air-gapped while the interface stays open to a model-backed planner later.

## Next milestone
- **Phase 07 — Integrations** (connector/plugin framework; real tool backends) on explicit
  go-ahead. Not started.

## Documentation gaps
- None blocking. Connector, persistence, and model-planner docs will land with those features.

## Final status
- **COMPLETE** — implementation + tests + security validation (release-blocking safety suite) +
  technical *and* user documentation delivered and verified.
