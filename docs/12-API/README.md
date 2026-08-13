---
title: API — Overview
document_id: API-000
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Backend / API
audience: API consumers & producers
phase: Documentation Bootstrap (M000)
---

# 12 — API

> **Purpose.** Standards for designing, securing, and versioning APIs. **Status: MVP target.**

## Documents

- [APIStandards.md](./APIStandards.md) — design conventions.
- [Authentication.md](./Authentication.md) — identity & tokens.
- [Authorization.md](./Authorization.md) — RBAC/ABAC via OPA.
- [Versioning.md](./Versioning.md) — evolution & deprecation.
- [CoreDomainAPI.md](./CoreDomainAPI.md) — assets, alerts, incidents endpoints (Phase 02, CURRENT).
- [AIGatewayAPI.md](./AIGatewayAPI.md) — grounded Q&A, triage, knowledge, and cyber-intel endpoints (Phase 03/05, CURRENT).
- [AgentsAPI.md](./AgentsAPI.md) — agent investigation runs + approvals (Phase 06, CURRENT).
- [IntegrationsAPI.md](./IntegrationsAPI.md) — plugins + connector invocation (Phase 07, CURRENT).
- [AutomationAPI.md](./AutomationAPI.md) — playbook runs, approvals, and grounded reports (Phase 08, CURRENT).

## Contract-First

- OpenAPI (REST) and proto (internal gRPC) in `packages/contracts` are the source of
  truth; server stubs and typed clients (incl. frontend) are generated
  ([../05-Backend/APIArchitecture.md](../05-Backend/APIArchitecture.md)).

## Foundations

- Naming: [../00-Governance/NamingConventions.md](../00-Governance/NamingConventions.md) §4.
- Security: [../03-Architecture/SecurityArchitecture.md](../03-Architecture/SecurityArchitecture.md).
