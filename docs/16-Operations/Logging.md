---
title: Logging
document_id: OPS-002
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Ops / Backend
audience: All engineers
phase: Documentation Bootstrap (M000)
related:
  - ./Observability.md
  - ../10-Security/DataSecurity.md
---

# Logging

> **Purpose.** Define logging standards and the distinction between operational logs and
> the security **audit** trail.

## 1. Operational Logs

- **Structured JSON**, one event per line, with `trace_id`, `tenant_id` (where applicable),
  level, service, and message. No `print()`/unstructured logs
  ([../00-Governance/CodingStandards.md](../00-Governance/CodingStandards.md)).

## 2. Log Levels

- `DEBUG` (dev), `INFO`, `WARN`, `ERROR`. Sensitive data never logged; redact at source.

## 3. Audit Logs (Distinct)

- Immutable, tenant-scoped, attributable records of authN/authZ decisions, AI calls, tool
  executions, approvals, and data access — separate from operational logs, longer
  retention ([../10-Security/DataSecurity.md](../10-Security/DataSecurity.md)).

## 4. Secret & PII Safety

- Secret scanning + redaction filters prevent credential/PII leakage into logs; enforced
  in shared logging library.

## 5. Storage

- Loki for operational logs; audit logs stored in a tamper-evident store with strict
  access control.

## 6. Air-Gapped

- All logs stay within the enclave; export tooling produces sanitized diagnostics only.

## 7. Retention

- Per data class/policy; audit retained longer ([../03-Architecture/DataArchitecture.md](../03-Architecture/DataArchitecture.md)).
