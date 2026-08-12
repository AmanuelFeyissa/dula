---
title: Project State (Current Execution State)
document_id: STATE-000
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Engineering leadership
audience: All contributors (and future context recovery)
phase: Documentation Bootstrap (M000)
---

# PROJECT_STATE

> **Purpose.** Current, frequently-changing execution state. Update this on every
> meaningful change. For durable knowledge, see [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md).

## Current Snapshot

| Field | Value |
|-------|-------|
| **CURRENT PHASE** | Phase 01 — Foundation (COMPLETE) |
| **CURRENT MILESTONE** | M001 ✅ complete |
| **STATUS** | Phase 01 done. Foundation merged to `main` (PR #1); live end-to-end OIDC login verified against Keycloak |
| **LAST COMPLETED TASK** | Live OIDC check: `maya` token → `GET /api/v1/me` HTTP 200 with claims; readyz status-label fix + tests |
| **CURRENT TASK** | — (Phase 01 complete; awaiting go-ahead for Phase 02) |
| **NEXT TASK** | Phase 02 — Core Platform (NOT started; do not begin without direction) |
| **BLOCKERS** | None. GitHub repo live: github.com/AmanuelFeyissa/dula (private) |

## What Exists

- `docs/` — full engineering handbook (reviewed in M000); `docs/adr/` — ADR-0001…0011 (Accepted).
- **Monorepo `dula`** on private GitHub with CI (docs/python/web/security gates green).
- `packages/common-py` (config, JSON logging, OIDC verifier); `apps/platform-api`
  (FastAPI healthz/readyz + `/api/v1/me`, Postgres + Alembic + RLS); `apps/web` (Next.js
  Keycloak login shell); Keycloak `dula` realm; OPA authz policy; Docker Compose dev stack.
- No models/datasets yet; domain services beyond identity start in Phase 02.

## What Is Next

**Phase 01 is complete.** Phase 02 — Core Platform
([04-MVP-Roadmap/Phase02-CorePlatform.md](./04-MVP-Roadmap/Phase02-CorePlatform.md)) is the
next milestone (M002) but has **not** started; begin only when directed. Remaining
non-blocking open items: API gateway tech + plugin sandbox mechanism (see
[00-Governance/ArchitectureDecisionRecords.md](./00-Governance/ArchitectureDecisionRecords.md)).

## Milestone Ledger

| Milestone | Phase | Status |
|-----------|-------|--------|
| M000 | Documentation Bootstrap | ✅ Docs complete + reviewed; ADR-0001…0011 Accepted |
| M001 | Phase 01 — Foundation | ✅ Complete (PR #1 merged; live OIDC verified) |
| M002+ | Phases 02–11 | ⏳ Not started |

## Open Items Requiring Human Action

- Sign off the reviewed foundation and ADR-0001…0010.
- Decide remaining open items (API gateway, sandbox mechanism, monorepo confirmation).
- Verify **REQUIRES RESEARCH** items before they inform implementation
  (see [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md) §8 and
  [PROJECT_REVIEW-M000.md](./PROJECT_REVIEW-M000.md) §9).
- Accept the residual risks or adjust scope (resourcing, air-gapped GPU/UX — review §12).

## Change Log

- 2026-08-11 — M000 documentation foundation created (AI-assisted, Draft).
- 2026-08-11 — Product naming decided: **Dula** / **Dula AI** (ADR-0001); all docs renamed.
- 2026-08-11 — M000 architecture & documentation review completed
  ([PROJECT_REVIEW-M000.md](./PROJECT_REVIEW-M000.md)); ADR-0001…0010 Accepted; contradictions
  (vector DB, event bus, agent runtime), MVP over-scope, and cross-tenant AI isolation
  resolved in the affected docs.
- 2026-08-11 — **Decisions promoted from MVP-staging to permanent, production-grade.**
  ADR-0002/0003/0004 revised: vector store = **Qdrant**, search/log-analytics =
  **OpenSearch**, event backbone = **Redpanda (Kafka API)**, **Go** approved for the
  data-plane. All "for MVP / on trigger / migrate later" staging removed across the docs;
  the chosen stack is now the permanent target (changeable only via a superseding ADR if a
  materially better technology emerges).
- 2026-08-12 — **Phase 01 (M001) build.** Monorepo initialized (ADR-0011) and pushed to
  private GitHub repo `AmanuelFeyissa/dula`. Delivered: root tooling (uv/ruff/mypy strict,
  pnpm/tsc), Docker Compose dev stack, CI gates; `packages/common-py` (config, JSON logging,
  OIDC verifier); `apps/platform-api` (FastAPI healthz/readyz + `/api/v1/me`, DB, Alembic
  initial migration with RLS); Keycloak `dula` realm export; OPA authz policy (+tests);
  `apps/web` Next.js login shell (Keycloak OIDC). Verified: ruff clean, mypy strict clean
  (19 files), 8 pytest pass, web builds, migration applied+rolled back on live Postgres.
- 2026-08-12 — **Phase 01 (M001) complete.** PR #1 merged to `main`; CI green
  (docs/python/web/security). Live end-to-end OIDC verified: Keycloak issued `maya` a token
  (aud `dula-api`, tenant_id, role `analyst`) and `GET /api/v1/me` returned HTTP 200 with the
  verified claims. Fixed a `/readyz` status-label bug (reported `degraded` while DB was ok)
  and added regression tests (10 pytest total).
