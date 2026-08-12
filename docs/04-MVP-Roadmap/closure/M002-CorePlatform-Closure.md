---
title: Milestone Closure — M002 (Phase 02 Core Platform)
document_id: MVP-M002-CLOSURE
status: Reviewed
version: 1.0.0
last_updated: 2026-08-12
owner: Engineering
audience: Project Maintainer, Developer, Architect, Security Engineer, DevOps/SRE
phase: Phase 02 — Core Platform (M002)
related:
  - ../Phase02-CorePlatform.md
  - ../../PROJECT_STATE.md
  - ./README.md
---

# Milestone Closure — M002

> Produced per **CLAUDE.md §11.8**.

- **Milestone identifier:** M002
- **Milestone name:** Phase 02 — Core Platform
- **Objective:** Deliver the core domain services (alerts, incidents, assets), the event bus
  + workers, service-layer RBAC/ABAC via OPA, tenant-isolation baseline, and an authenticated
  UI app shell with entity list/detail views — see [../Phase02-CorePlatform.md](../Phase02-CorePlatform.md).
- **Scope:** Domain data model + APIs; Redpanda event backbone producer + a worker consumer;
  OPA enforcement at the service layer; multi-tenancy isolation (repository scoping + RLS);
  UI navigation and read views. Out of scope: RAG/LLM, agents, plugins, models, and UI write
  forms (later phases).

## Implemented functionality
- **Domain entities:** `assets`, `incidents`, `alerts` (tenant-scoped, soft-deletable) and
  append-only `audit_events` (migration `0002_domain_spine`, RLS on every tenant table).
- **APIs:** full CRUD under `/api/v1/{assets,incidents,alerts}` with pagination, tenant
  scoping, per-action OPA authorization, audit logging, and domain-event emission
  ([../../12-API/CoreDomainAPI.md](../../12-API/CoreDomainAPI.md)).
- **Ports & adapters:** tenant-scoped repositories + application services own each unit of
  work (mutate → audit → commit → best-effort publish).
- **Event backbone:** shared `EventPublisher` (Redpanda/Kafka, graceful degradation) and
  `apps/worker` — an idempotent (dedupe-by-`event.id`) consumer with manual offset commits.
- **AuthZ:** `dula.authz` OPA policy expanded to the domain (roles analyst/hunter/responder/
  engineer/admin); a `require(action)` dependency enforces it at the service layer, fails
  closed, and audits denies. OPA added to the dev stack.
- **UI:** authenticated Next.js app shell with navigation and list/detail views for alerts,
  incidents, and assets via a typed server-side API client that forwards the access token.

## Technical / Architecture / Database / API / Security / AI-ML changes
- **Architecture:** ports-and-adapters layering realized (routers → authz → services →
  repositories → DB); event producer/consumer substrate established.
- **Database:** `0002_domain_spine` adds four tables, indexes, and RLS policies; downgrade
  restores Phase 01 state. Soft delete via `deleted_at`.
- **API:** 15 domain endpoints (5 per resource); API version bumped to `0.2.0`.
- **Security:** service-layer OPA enforcement (default-deny, fail-closed); tenant scoping at
  the repository layer + RLS defense-in-depth; immutable audit trail of data access and authZ
  denies; input validation via Pydantic. `packages/common-py` gained `opa` and `events`.
- **AI/ML:** none this milestone (N/A).

## Testing performed
- `ruff` clean; `ruff format --check` clean; `mypy --strict` clean (40 source files).
- `pytest` **26 passed** (5 integration skip automatically without a DB).
- **OPA policy tests 11/11** (`opa test deploy/opa/policy`).
- `next build` (web) succeeds — 9 routes compiled, lint + types pass.

## Security validation performed
- **Tenant isolation** proven by integration tests: tenant B cannot read, update, or delete
  tenant A's rows (404, no leak); soft-deleted rows are hidden.
- **AuthZ:** deny path returns 403 and writes an audit row; OPA client fails closed when OPA
  is unreachable (unit test). Live OPA decisions verified via the Data API.
- **Untrusted input:** enum/length validation at the schema layer; cross-tenant link
  references rejected as 404.

## Deployment validation
- `docker compose` brings up Postgres, OPA, and Redpanda. Alembic `upgrade head`,
  `downgrade base`, and re-`upgrade head` verified on live Postgres (RLS + policies present on
  all five tenant tables). **Live event round-trip** verified: publish → Redpanda → consume →
  idempotent processing (duplicate skipped). Worker Dockerfile added.
- **K8s dev/staging deploy — DEFERRED:** Helm charts/cluster are a later infra phase
  (§10.3 Phase 09–10); not available in this environment. Tracked as a known limitation.

## Documentation Impact Assessment (CLAUDE.md §11.6)
1. **Implemented:** domain CRUD, events + worker, OPA enforcement, tenant isolation, UI shell.
2. **Technical docs created:** [../../12-API/CoreDomainAPI.md](../../12-API/CoreDomainAPI.md);
   this closure report; the Phase 02 Completion Review.
3. **Technical docs updated:** `12-API/README.md`, `12-API/Authorization.md`,
   `07-Database/DataModel.md`, `03-Architecture/DataArchitecture.md`, `PROJECT_STATE.md`,
   `PROJECT_CONTEXT.md`, `SUMMARY.md`, `Glossary.md`.
4. **User docs created:** [../../17-User-Documentation/CoreEntitiesUserGuide.md](../../17-User-Documentation/CoreEntitiesUserGuide.md).
5. **User docs updated:** `17-User-Documentation/README.md` (guide set + current state).
6. **Intentionally not created (N/A):** RAG, Agent, Plugin/Integration, Model, AI/LLM,
   Performance, DR/Backup guides — that functionality does not exist yet.
7. **Examples/commands verified:** yes — migration, OPA decisions, event round-trip, and API
   examples were executed during closure.
8. **Links valid:** yes — `tools/check-doc-links.sh` passes.
9. **Screenshots/diagrams:** existing Mermaid diagrams remain accurate; no new ones required.
10. **Incomplete items:** UI write forms and full E2E-in-CI are FUTURE by design.
11. **Known documentation gaps:** admin/operator guides pending those features.

## Milestone Documentation Checklist (CLAUDE.md §11.7)
### Technical
- [x] Architecture updated · [x] API documentation updated (CoreDomainAPI)
- [x] Database documentation updated · [x] Configuration documented (settings/env)
- [x] Security documentation updated · [x] Deployment documentation updated (compose/OPA)
- [x] Testing documentation updated (closure) · [~] Troubleshooting (user guide section)
- [x] Operational documentation updated (worker/events) · [N/A] AI/ML · [N/A] RAG · [N/A] Agent
- [N/A] Plugin/integration
### User
- [x] Feature documentation (Core Entities User Guide) · [~] Getting Started (interim root README)
- [N/A] Installation · [N/A] Configuration guide · [~] User guide (core entities) · [N/A] Admin
- [N/A] Operator guide · [x] Troubleshooting (in guide) · [N/A] FAQ
### Quality
- [x] Front matter · [x] Naming · [x] Relative links validated · [x] Mermaid still valid
- [x] Commands verified · [x] Config examples verified · [x] API examples verified
- [x] No undocumented implemented functionality · [x] No implemented-as-FUTURE
- [x] No FUTURE-as-CURRENT · [x] Added to SUMMARY.md · [x] Glossary terms added
- [x] PROJECT_CONTEXT.md updated · [x] PROJECT_STATE.md updated

## Known limitations / issues / deferred work
- **K8s dev/staging deployment deferred** to the infrastructure phase (Helm/Argo CD, §10.3).
- **RLS not FORCEd**: the app still connects as the DB owner in dev; tenant isolation is
  enforced at the repository layer today. Dedicated non-owner app role + `FORCE ROW LEVEL
  SECURITY` remains Phase 09 hardening (carried over from M001).
- **UI is read-only** (list/detail); create/update/delete forms are a later phase — writes go
  through the API for now.
- **E2E not in CI**: Playwright smoke tests exist and run locally against the full stack;
  wiring them into CI (with Keycloak) is deferred.
- **Idempotency store is in-memory** in the worker; a durable store (Redis/Postgres) replaces
  it at scale. Event delivery uses a single shared topic.

## Lessons learned
- OPA's `rego.v1` requires `import rego.v1` (not the older `future.keywords` set) and has no
  `|` set-union operator; the policy was restructured accordingly, and policy tests now run in
  a container during verification.
- Keeping event publishing best-effort (degrade when the bus is down) preserved the
  air-gapped/deploy-anywhere guarantee without complicating the request path.

## Next milestone / gaps / status
- **Next milestone:** M003 — Phase 03 (Knowledge & RAG).
- **Documentation gaps:** admin/operator and UI-write guides pending those features.
- **Final status:** **COMPLETE** (required technical + user documentation present and verified).
