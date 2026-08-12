---
title: Plugin Lifecycle
document_id: PLG-002
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Integrations / Security
audience: Integration & security engineers
phase: Documentation Bootstrap (M000)
related:
  - ./PluginFramework.md
  - ./PluginSecurity.md
---

# Plugin Lifecycle

> **Purpose.** Define the lifecycle of a plugin from installation to removal, with security
> gates at each step.

## 1. Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Submitted
    Submitted --> Verified: signature + manifest valid
    Verified --> Reviewed: security review (marketplace)
    Reviewed --> Installed
    Installed --> Enabled: scoped permissions granted
    Enabled --> Upgraded
    Upgraded --> Enabled
    Enabled --> Disabled
    Disabled --> Removed
    Removed --> [*]
    Enabled --> Revoked: compromise detected
    Revoked --> Removed
```

## 2. Gates

- **Verify:** signature + manifest schema ([./PluginSecurity.md](./PluginSecurity.md)).
- **Review:** security review for marketplace/third-party plugins.
- **Enable:** grant only manifest-declared, least-privilege permissions.
- **Revoke:** fleet-wide disable of compromised plugins.

## 3. Upgrades

- New signed version verified; permission changes re-reviewed if the manifest requests
  more; rollback supported.

## 4. Air-Gapped

- Install/upgrade via offline bundle import; no external fetch
  ([../11-Deployment/AirGappedDeployment.md](../11-Deployment/AirGappedDeployment.md)).

## 5. Monitoring

- Enabled plugins are monitored (health, resource use, anomalies); alerts feed the incident
  process ([../16-Operations/Monitoring.md](../16-Operations/Monitoring.md)).
