---
title: Security Testing
document_id: SEC-008
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Security / QA
audience: Security, QA, engineers
phase: Documentation Bootstrap (M000)
related:
  - ../15-Testing/SecurityTesting.md
  - ./AIThreatModel.md
  - ./SecureDevelopment.md
---

# Security Testing (Program)

> **Purpose.** Define the security testing program that validates the threat-model
> mitigations. Test-suite mechanics live in
> [../15-Testing/SecurityTesting.md](../15-Testing/SecurityTesting.md); this is the
> security-owned program view.

## 1. Test Types

| Type | What | Cadence |
|------|------|---------|
| SAST | Static code analysis | Every PR |
| Dependency/CVE + license | Third-party risk | Every PR + scheduled |
| Secret scanning | Leaked credentials | Every PR |
| Container/image scan | Image vulns/config | Every build |
| DAST | Running-app testing | Against staging |
| IaC scanning | Misconfig in Helm/Terraform | Every PR |
| AI red-teaming | Injection, jailbreak, exfiltration | Per AI change + release |
| Pen testing | Manual/authorized | Periodic + pre-major-release |

## 2. AI-Specific Testing

- Adversarial suites for the AI threat model (T1–T12) integrated into the eval gate
  ([./AIThreatModel.md](./AIThreatModel.md),
  [../08-AI/EvaluationStrategy.md](../08-AI/EvaluationStrategy.md)).

## 3. Gating

- Critical/high findings block release; findings tracked to remediation with SLAs.

## 4. Coverage Mapping

- Each threat-model mitigation maps to at least one test; gaps are tracked as risks in
  [../PROJECT_CONTEXT.md](../PROJECT_CONTEXT.md).

## 5. Reporting

- Results feed dashboards ([../16-Operations/Monitoring.md](../16-Operations/Monitoring.md))
  and the incident process for exploited/serious findings.

## Related Documents

- [../15-Testing/SecurityTesting.md](../15-Testing/SecurityTesting.md) ·
  [./SecureDevelopment.md](./SecureDevelopment.md)
