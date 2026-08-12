---
title: Phase 01 — Foundation
document_id: MVP-001
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Platform / Backend
audience: All contributors
phase: Documentation Bootstrap (M000)
related:
  - ./MVPOverview.md
  - ../01-Project/ProjectStructure.md
---

# Phase 01 — Foundation

> **Purpose.** Turn the empty repo into a working engineering baseline: structure, CI/CD,
> local dev, auth, database, and the first thin service — the skeleton everything else
> hangs on.

## Objective
Establish repository, tooling, CI/CD, local dev, identity, and persistence so features can
be built safely.

## Scope
- Monorepo scaffolding ([../01-Project/ProjectStructure.md](../01-Project/ProjectStructure.md)).
- CI/CD with lint/type/test/security gates ([../00-Governance/RepositoryGovernance.md](../00-Governance/RepositoryGovernance.md)).
- Docker Compose local stack ([../11-Deployment/LocalDevelopment.md](../11-Deployment/LocalDevelopment.md)).
- Keycloak (authN) + OPA (authZ) baseline; PostgreSQL + Alembic; shared libraries
  (config, logging, telemetry).
- First thin API service + UI shell (login only).
- First ADRs (ADR-0001..0002, and others as decided).

## Dependencies
- M000 documentation approved.

## Deliverables
- Running local stack via one command; CI green on a trivial change; login works end-to-end;
  base Helm charts scaffolded.

## Implementation Requirements
- Standards enforced ([../00-Governance/CodingStandards.md](../00-Governance/CodingStandards.md));
  contract-first API setup ([../12-API/README.md](../12-API/README.md)).

## Tests
- Unit + a smoke integration test; CI gates active
  ([../15-Testing/TestingStrategy.md](../15-Testing/TestingStrategy.md)).

## Security Requirements
- Secret management wired (Vault/SOPS), no secrets in repo; SAST/secret/dep scans in CI
  ([../10-Security/SecureDevelopment.md](../10-Security/SecureDevelopment.md)); authN/authZ
  baseline.

## Documentation
- Update [../PROJECT_STATE.md](../PROJECT_STATE.md); developer setup guide; ADRs recorded.

## Acceptance Criteria
- A new engineer can clone, run one command, log in, and pass CI.

## Definition of Done
- Global DoD ([./MVPOverview.md](./MVPOverview.md) §5) + above criteria met and reviewed.

## Implementation Status (2026-08-12, M001)

| Deliverable | Status |
|-------------|--------|
| Monorepo scaffolding (ADR-0011) + private GitHub repo | ✅ Done |
| Root tooling (uv/ruff/mypy strict, pnpm/tsc, editorconfig) | ✅ Done |
| Docker Compose dev stack (Postgres, Redis, Qdrant, OpenSearch, MinIO, Redpanda, Keycloak) | ✅ Done (compose validates; Postgres run + migration verified) |
| CI (docs link-check + naming, ruff/mypy/pytest, web build, gitleaks) | ✅ Authored; first cloud run pending push |
| `packages/common-py` (config, JSON logging, OIDC verifier) | ✅ Done (tests pass) |
| `apps/platform-api` (healthz/readyz, `/api/v1/me`, DB, Alembic + RLS) | ✅ Done (ruff/mypy/pytest green; migration applied+rolled back) |
| Keycloak `dula` realm export (client `dula-web`, user `maya`) | ✅ Done (import wired into compose) |
| OPA authz policy (`dula.authz`) + policy tests | ✅ Done (enforcement middleware lands Phase 02) |
| `apps/web` Next.js OIDC login shell → calls `/api/v1/me` | ✅ Built + typechecks; **live end-to-end login pending a stack run** |

**Remaining to fully close acceptance:** a live end-to-end login test (`make up` → run
platform-api → `pnpm --filter web dev` → sign in as `maya/maya`) and the first green CI run
on GitHub. Both are runtime checks; all code/config is in place.
