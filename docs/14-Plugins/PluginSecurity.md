---
title: Plugin Security (Framework)
document_id: PLG-004
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Security / Integrations
audience: Security & integration engineers
phase: Documentation Bootstrap (M000)
related:
  - ../10-Security/PluginSecurity.md
  - ./PluginFramework.md
  - ./PluginLifecycle.md
---

# Plugin Security (Framework View)

> **Purpose.** The framework-level controls implementing the security policy in
> [../10-Security/PluginSecurity.md](../10-Security/PluginSecurity.md). That document is
> the authoritative policy; this is how the framework enforces it.

## 1. Enforcement Controls

| Control | Mechanism |
|---------|-----------|
| Signing | Verify signature on install/upgrade |
| Manifest least privilege | Grant only declared permissions |
| Sandbox | Isolated execution (mechanism REQUIRES DECISION), non-root, read-only FS, resource limits |
| Egress allowlist | Default-deny network; only declared endpoints |
| Scoped secrets | Vault-injected, per-plugin, never shared/logged |
| Untrusted output | Treated as evidence, validated |
| Audit | All plugin actions logged |
| Revocation | Fleet-wide disable of compromised plugins |

## 2. Trust Model

- Plugins are **untrusted by default**, even first-party — the host enforces boundaries
  regardless of authorship.

## 3. Resource Governance

- CPU/memory/time/network quotas per plugin; abusive plugins throttled/halted.

## 4. Data Handling

- Plugins access only data within granted scope; tenant isolation preserved; no
  cross-tenant access ([../10-Security/DataSecurity.md](../10-Security/DataSecurity.md)).

## 5. Air-Gapped Behavior

- External-egress plugins are inert offline; no hidden phone-home
  ([../11-Deployment/AirGappedDeployment.md](../11-Deployment/AirGappedDeployment.md)).

## 6. Testing

- Plugin sandbox escape and egress-bypass tests are part of security testing
  ([../10-Security/SecurityTesting.md](../10-Security/SecurityTesting.md)).
