---
title: Integration & API Testing
document_id: TST-003
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Engineering / QA
audience: All engineers
phase: Documentation Bootstrap (M000)
related:
  - ./TestingStrategy.md
  - ../12-API/APIStandards.md
---

# Integration & API Testing

> **Purpose.** Verify services work with their real dependencies and honor API contracts.

## 1. Integration Tests

- Service tested against **real** dependencies in containers (Postgres, Redis, Qdrant,
  OpenSearch, Redpanda/Kafka) — not mocks — to catch wiring/query/migration issues.

## 2. Contract Tests

- Assert conformance to OpenAPI/proto contracts in `packages/contracts`; prevent breaking
  changes ([../12-API/Versioning.md](../12-API/Versioning.md)).

## 3. API/E2E Flows

- Cover key use-case flows (e.g. UC-01 triage) end-to-end via the API; UI E2E via
  Playwright ([../02-Vision/UseCases.md](../02-Vision/UseCases.md)).
- **CURRENT**: `apps/web/e2e/` — per-persona specs (analyst triage, responder approval, admin
  integrations, second-tenant isolation) plus an axe accessibility sweep, run manually against
  the local dev stack (`pnpm --filter web e2e`; not wired into CI — `playwright.config.ts`
  explains why). Not run automatically yet; a future phase may add a CI lane that stands up the
  full stack first.

## 4. Tenant Isolation Tests

- Explicit tests that a tenant cannot read/act on another tenant's data (RLS + authZ +
  index namespacing) ([../10-Security/DataSecurity.md](../10-Security/DataSecurity.md)).

## 5. Migration Tests

- Apply-forward (prod-like) and apply/rollback (dev) validated
  ([../07-Database/MigrationStrategy.md](../07-Database/MigrationStrategy.md)).

## 6. External Systems

- Connectors tested against recorded fixtures; **no live external calls in CI**
  ([../14-Plugins/ConnectorStandards.md](../14-Plugins/ConnectorStandards.md)).

## 7. Environments

- Ephemeral test environments spun up in CI; teardown after runs.
