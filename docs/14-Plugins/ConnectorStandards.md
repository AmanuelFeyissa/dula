---
title: Connector Standards
document_id: PLG-003
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Integrations
audience: Integration engineers
phase: Documentation Bootstrap (M000)
related:
  - ./PluginFramework.md
  - ../03-Architecture/IntegrationArchitecture.md
---

# Connector Standards

> **Purpose.** Define consistent contracts for connectors so integrations behave
> predictably and safely.

## 1. Capability Naming

- `<system>.<capability>` (e.g. `splunk.search`, `vt.lookup_hash`, `edr.isolate_host`).
- Read vs consequential capabilities are explicitly classified (drives approval —
  [../13-Agents/HumanApproval.md](../13-Agents/HumanApproval.md)).

## 2. Contract Shape

- Typed input/output schemas; normalized outputs mapping to internal models
  ([../07-Database/DataModel.md](../07-Database/DataModel.md)); errors standardized.
- Prefer open standards where applicable: STIX/TAXII (intel), Sigma (detections), YARA
  (malware).

## 3. Idempotency & Pagination

- Read capabilities support pagination; side-effecting capabilities support idempotency
  keys ([../12-API/APIStandards.md](../12-API/APIStandards.md)).

## 4. Auth & Secrets

- External credentials scoped, sourced from Vault, injected at runtime, never logged
  ([../10-Security/DataSecurity.md](../10-Security/DataSecurity.md)).

## 5. Egress & SSRF

- Declared egress endpoints only; URL validation; default-deny beyond the allowlist
  ([../10-Security/ThreatModel.md](../10-Security/ThreatModel.md)).

## 6. Rate Limits & Resilience

- Respect external system limits; retries with backoff for idempotent reads; circuit
  breakers.

## 7. Testing

- Contract tests + recorded fixtures; no live external calls in CI
  ([../15-Testing/IntegrationTesting.md](../15-Testing/IntegrationTesting.md)).

## 8. Documentation

- Each connector documents capabilities, schemas, required permissions, and egress needs.
