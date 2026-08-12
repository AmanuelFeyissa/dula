---
title: Phase 02 — Core Platform
document_id: MVP-002
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Backend / Frontend
audience: All contributors
phase: Documentation Bootstrap (M000)
related:
  - ./Phase01-Foundation.md
  - ../03-Architecture/ComponentArchitecture.md
---

# Phase 02 — Core Platform

> **Purpose.** Build the core domain model and platform services users interact with,
> including async processing — the substrate RAG/AI features will use.

## Objective
Deliver core domain services (alerts, incidents, assets), the UI application shell with
real navigation, RBAC enforcement, and the event bus + workers.

## Scope
- Domain services + data models ([../07-Database/DataModel.md](../07-Database/DataModel.md)).
- Event & streaming backbone (**Redpanda / Kafka API**) + workers ([../03-Architecture/DataArchitecture.md](../03-Architecture/DataArchitecture.md)).
- RBAC/ABAC enforcement via OPA ([../12-API/Authorization.md](../12-API/Authorization.md)).
- UI: authenticated app shell, entity list/detail views.
- Multi-tenancy isolation (RLS + scoping) baseline (ADR-0006).

## Dependencies
- Phase 01 complete.

## Deliverables
- Create/read/update core entities via API + UI; events flowing to workers; tenant
  isolation enforced and tested.

## Implementation Requirements
- Ports & adapters ([../05-Backend/ServiceArchitecture.md](../05-Backend/ServiceArchitecture.md));
  idempotent consumers; generated API client for UI.

## Tests
- Integration tests with real deps; **tenant isolation tests**; contract tests; UI E2E for
  core flows ([../15-Testing/IntegrationTesting.md](../15-Testing/IntegrationTesting.md)).

## Security Requirements
- AuthZ at service layer; audit logging of data access; input validation
  ([../10-Security/DataSecurity.md](../10-Security/DataSecurity.md)).

## Documentation
- Update data model, API reference, PROJECT_STATE; ADR-0006 recorded.

## Acceptance Criteria
- A user can manage core entities within their tenant; cross-tenant access is provably
  blocked.

## Definition of Done
- Global DoD + above; deploys to a K8s dev/staging environment.
