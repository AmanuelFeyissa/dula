---
title: Data Security
document_id: SEC-006
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Security
audience: Security, backend & platform engineers
phase: Documentation Bootstrap (M000)
related:
  - ../03-Architecture/DataArchitecture.md
  - ./ThreatModel.md
---

# Data Security

> **Purpose.** Define protection of data at rest, in transit, and in use; secrets
> management; classification; retention; and privacy — for highly sensitive security data.

## 1. Classification

| Class | Examples | Handling |
|-------|----------|----------|
| Public | Public standards (ATT&CK, CVE) | Normal |
| Internal | Config, non-sensitive metadata | AuthZ-gated |
| Sensitive | Customer logs, incidents, TI, PII | Encrypted, strict authZ, audited, RAG-eligibility controlled |
| Secret | Credentials, keys, tokens | Vault only; never in code/logs/context |

## 2. Encryption

- **In transit:** TLS everywhere; mTLS between services.
- **At rest:** encrypted PostgreSQL, object storage, and backups; key management via Vault
  / KMS (**REQUIRES DECISION** per profile; air-gapped uses on-prem KMS/Vault).
- **In use:** minimize sensitive data in memory/logs; redact in telemetry.

## 3. Secrets Management

- HashiCorp Vault for runtime secrets and dynamic credentials; SOPS for encrypted config
  in Git (GitOps). **No secrets in code, images, or logs.** Secret scanning in CI.

## 4. Tenant Isolation

- Defense-in-depth: application scoping + PostgreSQL RLS (`tenant_id`) + per-tenant index
  namespaces + per-tenant object prefixes
  ([../03-Architecture/SystemArchitecture.md](../03-Architecture/SystemArchitecture.md)).

## 5. Privacy

- No PII in training data; de-identify telemetry before any AI/analytics use
  ([../08-AI/DatasetStrategy.md](../08-AI/DatasetStrategy.md)).
- Data-subject/retention obligations configurable per tenant.

## 6. Retention & Deletion

- Per-class, per-tenant retention; secure deletion; audit data retained longer under its
  own policy ([../03-Architecture/DataArchitecture.md](../03-Architecture/DataArchitecture.md)).

## 7. Audit Data

- Immutable, tenant-scoped, attributable; covers authN/authZ, AI calls, tool executions,
  and data access ([../16-Operations/Logging.md](../16-Operations/Logging.md)).

## 8. AI Data-Leak Controls

- authZ at retrieval, output filtering, and no-secrets-in-context prevent model-mediated
  disclosure ([./AIThreatModel.md](./AIThreatModel.md) T5).
