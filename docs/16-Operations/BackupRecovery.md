---
title: Backup & Recovery
document_id: OPS-005
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Ops / Platform
audience: Ops & platform engineers
phase: Documentation Bootstrap (M000)
related:
  - ../11-Deployment/DisasterRecovery.md
  - ../07-Database/DatabaseArchitecture.md
---

# Backup & Recovery

> **Purpose.** Define what is backed up, how, and how restores are verified. Complements
> DR ([../11-Deployment/DisasterRecovery.md](../11-Deployment/DisasterRecovery.md)).
>
> **Delivered (Phase 09):** Postgres backup/restore scripts with checksum verification at
> `deploy/backup/` (`pg-backup.sh`, `pg-restore.sh`); the other stateful tiers (Qdrant, OpenSearch,
> MinIO, Redpanda) use their native snapshot/replication mechanisms. Scripts are syntax-checked in
> CI; the **live restore drill** meeting RPO/RTO is operational ([../11-Deployment/GAReadiness.md](../11-Deployment/GAReadiness.md)).

## 1. Backup Scope

| Data | Method |
|------|--------|
| PostgreSQL | Regular dumps + PITR where supported |
| Object storage | Versioned/replicated backups |
| Vector/search indices | Backup or rebuild from source of record |
| Secrets (Vault) | Vault's own backup/seal procedures |
| Config (GitOps) | In Git (SOPS-encrypted) |
| Model artifacts | Registry/object storage backups |
| Audit logs | Backed up with integrity preserved |

## 2. Schedule & Retention

- Frequency and retention per data class/customer policy (**REQUIRES DECISION**); audit
  and system-of-record prioritized.

## 3. Restore Verification

- Restores are **tested** regularly; an untested backup is treated as non-existent.
- Rebuild derived stores (vector/search) from source when faster/safer.

## 4. Encryption & Storage

- Backups encrypted; stored redundantly/offsite where the profile allows; air-gapped
  backups stay within the enclave.

## 5. Runbooks

- Step-by-step restore procedures in [./OperationalRunbooks.md](./OperationalRunbooks.md).

## 6. RPO/RTO

- Targets set per deployment ([../11-Deployment/DisasterRecovery.md](../11-Deployment/DisasterRecovery.md)).
