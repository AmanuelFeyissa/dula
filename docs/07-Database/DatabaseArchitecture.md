---
title: Database Architecture
document_id: DB-002
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Data / Backend
audience: Backend & data engineers
phase: Documentation Bootstrap (M000)
related:
  - ../03-Architecture/DataArchitecture.md
  - ./MigrationStrategy.md
---

# Database Architecture

> **Purpose.** Define the databases, their roles, isolation, and operational shape.
> Complements [../03-Architecture/DataArchitecture.md](../03-Architecture/DataArchitecture.md).

## 1. Datastores & Roles

| Store | Role |
|-------|------|
| PostgreSQL 16 | System of record (transactional entities, audit) with RLS tenancy |
| Qdrant | RAG embeddings (standard vector store) |
| OpenSearch | Full-text/BM25 + log analytics |
| Redis | Cache, rate limiting, ephemeral queues |
| Object storage (MinIO/S3) | Files, artifacts, models, reports |

## 2. Tenancy Isolation

- PostgreSQL **Row-Level Security** keyed on `tenant_id`; app injects tenant scope; vector/
  search indices namespaced per tenant; object storage prefixed per tenant. Defense-in-depth
  ([../10-Security/DataSecurity.md](../10-Security/DataSecurity.md)).

## 3. Ownership

- Each service owns its schema/tables; no cross-service table access — integration via API
  or events ([../05-Backend/ServiceArchitecture.md](../05-Backend/ServiceArchitecture.md)).

## 4. Consistency Model

- Postgres is strongly consistent (source of truth). Derived stores (vector/search) are
  eventually consistent, rebuilt from source when needed
  ([../11-Deployment/DisasterRecovery.md](../11-Deployment/DisasterRecovery.md)).

## 5. Performance

- Indexing per access patterns; connection pooling; read replicas if needed (later).
- Partitioning for high-volume tables (e.g. events) — evaluated as volume grows.

## 6. Operations

- Backups, PITR where supported, and DR ([../16-Operations/BackupRecovery.md](../16-Operations/BackupRecovery.md)).
- Runs self-hosted via operators (on-prem/air-gapped) or managed (cloud, optional).

## 7. Encryption

- At rest and in transit; keys via Vault/KMS
  ([../10-Security/DataSecurity.md](../10-Security/DataSecurity.md)).
