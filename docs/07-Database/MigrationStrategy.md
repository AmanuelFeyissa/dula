---
title: Migration Strategy
document_id: DB-003
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Backend / Data
audience: Backend engineers
phase: Documentation Bootstrap (M000)
related:
  - ./DatabaseArchitecture.md
  - ../01-Project/ReleaseStrategy.md
---

# Migration Strategy

> **Purpose.** Define safe schema evolution across all deployment profiles.

## 1. Tooling

- **Alembic** migrations, version-controlled in the owning service; no manual production
  DDL.

## 2. Rules

- **Forward-only in production**; reversible in dev where feasible.
- **Backward-compatible / expand-contract** for zero-downtime:
  1. Expand (add nullable/new structures),
  2. Migrate/backfill,
  3. Switch code,
  4. Contract (remove old) in a later release.
- Migrations idempotent and tested against realistic data volumes.

## 3. Deployment Integration

- Migrations run as a controlled step before/with rolling deploys
  ([../11-Deployment/KubernetesDeployment.md](../11-Deployment/KubernetesDeployment.md));
  never automatically destructive.

## 4. Air-Gapped

- Migrations ship in the release/offline bundle and run locally; no external dependency.

## 5. Data Backfills

- Large backfills run as background jobs (workers), monitored, resumable, and idempotent.

## 6. Testing

- Migration tests in CI; apply-and-rollback (dev) and apply-forward (prod-like) validated
  ([../15-Testing/IntegrationTesting.md](../15-Testing/IntegrationTesting.md)).

## 7. Compatibility

- Coordinated with API/release versioning
  ([../01-Project/ReleaseStrategy.md](../01-Project/ReleaseStrategy.md)) so schema and code
  stay compatible during rollout.
