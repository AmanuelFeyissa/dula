# ADR-0006: Multi-Tenancy Isolation Model

- Status: Accepted
- Date: 2026-08-11
- Deciders: Architecture, Security
- Related: [../03-Architecture/SystemArchitecture.md](../03-Architecture/SystemArchitecture.md)

## Context
Dula serves enterprises and MSSPs (multi-tenant) and must isolate highly sensitive data,
including across the **AI/inference layer** — a gap identified in the M000 review (S1).

## Options Considered
1. **Shared services + strong logical isolation** (tenant_id + Postgres RLS + per-tenant
   index namespaces + object prefixes).
2. Dedicated instance per tenant (namespace/DB/serving) — strongest, costlier.
3. Application-only scoping — rejected (single missed check = crossover).

## Decision
- **Default: shared services with defense-in-depth logical isolation** —
  application scope **+** PostgreSQL RLS on `tenant_id` **+** per-tenant vector/search
  namespaces **+** per-tenant object-storage prefixes.
- **AI-layer isolation is mandatory:** no prompt/KV/response cache is shared across tenant
  boundaries; embeddings and retrieval are tenant-namespaced and authorization-filtered at
  retrieval time.
- **High-assurance option:** dedicated-instance isolation (separate namespace/DB/serving)
  offered as a deployment profile.

## Consequences
- Cost-efficient default with a strong isolation story; explicit AI-layer control closes the
  cross-tenant leakage risk. Requires dedicated isolation tests.

## Compliance / Verification
- Tenant-isolation integration tests (data + retrieval + cache) are release-blocking.
