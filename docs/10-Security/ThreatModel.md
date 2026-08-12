---
title: Platform Threat Model
document_id: SEC-001
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Security
audience: Security, architects, engineers
phase: Documentation Bootstrap (M000)
related:
  - ./AIThreatModel.md
  - ../03-Architecture/SecurityArchitecture.md
---

# Platform Threat Model

> **Purpose.** Identify assets, actors, trust boundaries, and threats to the platform
> (non-AI-specific threats are here; AI-specific threats in
> [AIThreatModel.md](./AIThreatModel.md)), with mitigations. Uses STRIDE as a lens.

## 1. Assets

- Customer security data (logs, alerts, incidents, TI) — highest sensitivity.
- Credentials/secrets for external integrations.
- Models and datasets (IP).
- The platform's control plane (auth, policy, agent runtime).
- Audit logs.

## 2. Actors

- External attacker (no access) · malicious/curious tenant user · compromised integration/
  data source · malicious plugin · insider · supply-chain attacker.

## 3. Trust Boundaries

See [../03-Architecture/SecurityArchitecture.md](../03-Architecture/SecurityArchitecture.md):
external↔edge, core↔sandboxed plugins/agent-tools, and the AI trust boundary.

## 4. STRIDE Summary

| Threat | Example | Mitigation |
|--------|---------|-----------|
| Spoofing | Forged identity/token | OIDC, short-lived JWT, mTLS service identity |
| Tampering | Alter data/config | Integrity checks, RLS, signed artifacts, audit |
| Repudiation | Deny an action | Immutable, attributable audit logs |
| Information disclosure | Cross-tenant/data leak | Tenant isolation (app+RLS+namespace), encryption, authZ at retrieval |
| Denial of service | Resource exhaustion | Rate limits, quotas, bulkheads, autoscale |
| Elevation of privilege | Gain higher access | Least privilege, OPA authZ, no implicit trust |

## 5. Specific Threats & Mitigations

- **API attacks (injection, IDOR, broken authZ):** input validation, parameterized
  queries, object-level authZ (OPA), contract validation
  ([../12-API/Authorization.md](../12-API/Authorization.md)).
- **SSRF (via connectors/outbound calls):** egress allowlists, URL validation, no
  fetching attacker-controlled URLs unfiltered ([../03-Architecture/IntegrationArchitecture.md](../03-Architecture/IntegrationArchitecture.md)).
- **Command injection / unsafe tool exec:** no shelling out with untrusted input;
  permissioned, sandboxed tools only ([./AgentSecurity.md](./AgentSecurity.md)).
- **Container compromise:** minimal images, non-root, read-only FS, seccomp, network
  policy, sandboxed plugins ([./PluginSecurity.md](./PluginSecurity.md)).
- **Secret leakage:** Vault, no secrets in code/logs, secret scanning
  ([./DataSecurity.md](./DataSecurity.md)).
- **Supply-chain attack:** signed images, SBOM, provenance, dependency scanning
  ([./SupplyChainSecurity.md](./SupplyChainSecurity.md)).
- **Multi-tenant crossover:** defense-in-depth isolation (see §4 Information disclosure).

## 6. Cross-Cutting Controls

- AuthN/AuthZ, encryption, audit, monitoring, least privilege, network segmentation,
  default-deny egress (essential for air-gapped assurance).

## 7. Review Cadence

- The threat model is reviewed each phase and when trust boundaries change (ADR-triggering).
  Security testing validates mitigations ([./SecurityTesting.md](./SecurityTesting.md)).
