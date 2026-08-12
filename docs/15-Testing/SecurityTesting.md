---
title: Security Testing (Suite)
document_id: TST-004
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Security / QA
audience: Security & QA engineers
phase: Documentation Bootstrap (M000)
related:
  - ../10-Security/SecurityTesting.md
  - ../10-Security/AIThreatModel.md
---

# Security Testing (Suite Mechanics)

> **Purpose.** The test-suite mechanics implementing the security testing program in
> [../10-Security/SecurityTesting.md](../10-Security/SecurityTesting.md) (authoritative
> program view).

## 1. Automated in CI

- SAST, dependency/CVE + license, secret scan, container scan, IaC scan — block on
  critical/high.

## 2. Dynamic (Staging)

- DAST against a running deployment; authenticated scans covering authZ/tenant isolation.

## 3. AI Red-Team Suite

- Automated adversarial tests for the AI threat model (T1–T12):
  - Prompt injection (direct/indirect), jailbreaks, data exfiltration attempts, tool-abuse
    attempts, cross-tenant retrieval attempts.
- Integrated into the AI eval gate ([../10-Security/AIThreatModel.md](../10-Security/AIThreatModel.md),
  [./AIEvaluation.md](./AIEvaluation.md)).

## 4. Isolation & Sandbox Tests

- Plugin sandbox-escape and egress-bypass tests; no-egress assertion for air-gapped
  ([../11-Deployment/AirGappedDeployment.md](../11-Deployment/AirGappedDeployment.md)).

## 5. Manual Pen Testing

- Periodic authorized pen tests and pre-major-release reviews; findings tracked to
  remediation SLAs.

## 6. Coverage Mapping

- Each threat-model mitigation maps to ≥1 test; gaps recorded as risks.
