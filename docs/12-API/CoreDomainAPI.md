---
title: Core Domain API (Assets, Alerts, Incidents)
document_id: API-004
status: Draft
version: 0.1.0
last_updated: 2026-08-12
owner: Backend / API
audience: Developer, API consumer
phase: Phase 02 — Core Platform (M002)
related:
  - ./APIStandards.md
  - ./Authentication.md
  - ./Authorization.md
  - ../07-Database/DataModel.md
  - ../17-User-Documentation/CoreEntitiesUserGuide.md
---

# Core Domain API

> **Purpose.** Reference for the Phase 02 domain endpoints on the Platform API — the SOC/IR
> spine of **assets**, **alerts**, and **incidents**. **Status: CURRENT** (implemented in
> `apps/platform-api`). User-facing guide:
> [../17-User-Documentation/CoreEntitiesUserGuide.md](../17-User-Documentation/CoreEntitiesUserGuide.md).

## Conventions

- Base path `/api/v1`; all domain endpoints require a Keycloak bearer token
  ([Authentication.md](./Authentication.md)). Missing/invalid token → **401**.
- Every request is scoped to the caller's tenant (the signed `tenant_id` claim). A token
  without a valid `tenant_id` → **403**. Objects of other tenants are invisible → **404**,
  never leaked (ADR-0006).
- Authorization is enforced per action via OPA before the handler runs; a denied action →
  **403** and is audited ([Authorization.md](./Authorization.md)).
- List endpoints page with `limit` (1–200, default 50) and `offset` (≥0, default 0) and
  return `{ items, total, limit, offset }`.
- Timestamps are RFC 3339 (UTC). IDs are UUIDv4.

## Endpoints

| Resource | Method & path | Action (OPA) | Success |
|----------|---------------|--------------|---------|
| Assets | `POST /api/v1/assets` | `assets.create` | 201 |
| Assets | `GET /api/v1/assets` | `assets.read` | 200 (page) |
| Assets | `GET /api/v1/assets/{id}` | `assets.read` | 200 |
| Assets | `PATCH /api/v1/assets/{id}` | `assets.update` | 200 |
| Assets | `DELETE /api/v1/assets/{id}` | `assets.delete` | 204 |
| Incidents | `POST /api/v1/incidents` | `incidents.create` | 201 |
| Incidents | `GET /api/v1/incidents` | `incidents.read` | 200 (page) |
| Incidents | `GET /api/v1/incidents/{id}` | `incidents.read` | 200 |
| Incidents | `PATCH /api/v1/incidents/{id}` | `incidents.update` | 200 |
| Incidents | `DELETE /api/v1/incidents/{id}` | `incidents.delete` | 204 |
| Alerts | `POST /api/v1/alerts` | `alerts.create` | 201 |
| Alerts | `GET /api/v1/alerts` | `alerts.read` | 200 (page) |
| Alerts | `GET /api/v1/alerts/{id}` | `alerts.read` | 200 |
| Alerts | `PATCH /api/v1/alerts/{id}` | `alerts.update` | 200 |
| Alerts | `DELETE /api/v1/alerts/{id}` | `alerts.delete` | 204 |

`DELETE` is a **soft delete** (sets `deleted_at`); soft-deleted rows are excluded from reads.

## Fields

- **Asset:** `name` (required), `asset_type` (`host|account|cloud_resource|k8s_resource|other`),
  `identifier`, `criticality` (`low|medium|high|critical`), `description`.
- **Incident:** `title` (required), `description`, `severity` (`info|low|medium|high|critical`),
  `status` (`open|investigating|contained|resolved|closed`), `assignee_subject`.
- **Alert:** `title` (required), `description`, `severity`, `status`
  (`new|triaged|in_progress|closed|false_positive`), `source`, `asset_id`, `incident_id`.
  Linked `asset_id`/`incident_id` must belong to the same tenant, else **404**.

Read responses also include `id`, `tenant_id`, `created_at`, `updated_at`.

## Events

Successful writes emit a `domain.entity.action` event (e.g. `alert.created`,
`incident.updated`, `asset.deleted`) to the event backbone
([../03-Architecture/DataArchitecture.md](../03-Architecture/DataArchitecture.md)).
Publishing is best-effort: if the bus is unavailable the write still succeeds
(deploy-anywhere / air-gapped principle).

## Example

```bash
TOKEN=... # Keycloak access token (aud: dula-api)
curl -sX POST http://localhost:8000/api/v1/alerts \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"title":"suspicious login","severity":"high","source":"edr"}'
```

## Auditing

Every create/update/delete and every authorization **deny** writes an immutable
`audit_events` row (actor, action, resource, decision) within the caller's tenant
([../10-Security/DataSecurity.md](../10-Security/DataSecurity.md)).
