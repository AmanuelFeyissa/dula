---
title: Disaster Recovery
document_id: DEP-007
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Ops / Platform
audience: Ops engineers
phase: Documentation Bootstrap (M000)
related:
  - ../16-Operations/BackupRecovery.md
  - ./KubernetesDeployment.md
---

# Disaster Recovery

> **Purpose.** Define recovery objectives and procedures for major failures, across
> profiles including air-gapped.

## 1. Objectives

- **RPO/RTO** targets are set per deployment/customer (**REQUIRES DECISION**); documented
  per install. Bootstrap does not assert specific numbers.

## 2. What Must Be Recoverable

- PostgreSQL (system of record), object storage (artifacts/models/reports), search/vector
  indices (rebuildable from source of record where possible), configuration, secrets
  (Vault), and audit logs.

## 3. Strategy

```mermaid
flowchart LR
    BK[Regular backups] --> STORE[(Offsite/redundant store)]
    STORE --> RESTORE[Restore procedure]
    RESTORE --> VERIFY[Verify + reconcile indices]
    VERIFY --> RESUME[Resume service]
```

- Regular, tested backups ([../16-Operations/BackupRecovery.md](../16-Operations/BackupRecovery.md)).
- Rebuild derived stores (vector/search indices) from the system of record + source
  content when faster/safer than restoring them.
- Model artifacts restored from registry/bundle.

## 4. Failover

- Multi-AZ/replica for HA (cloud/on-prem where infra allows); documented per profile.
- Air-gapped DR is entirely within the enclave (no external failover).

## 5. Testing

- DR drills validate restores and measured RPO/RTO; results recorded. Untested backups are
  treated as non-existent.

## 6. Runbooks

- Step-by-step recovery in [../16-Operations/OperationalRunbooks.md](../16-Operations/OperationalRunbooks.md).
