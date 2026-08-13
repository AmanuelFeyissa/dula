---
title: Plugin Security
document_id: SEC-005
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Security / Integrations
audience: Security, integration engineers
phase: Documentation Bootstrap (M000)
related:
  - ../03-Architecture/PluginArchitecture.md
  - ../14-Plugins/PluginSecurity.md
  - ./ThreatModel.md
---

# Plugin Security

> **Purpose.** Define the security model for plugins/connectors — third-party or
> first-party extensions that run inside the platform and talk to external systems.
> Detailed framework rules also in [../14-Plugins/PluginSecurity.md](../14-Plugins/PluginSecurity.md).

## 1. Threats

- Malicious/compromised plugin exfiltrating data, escalating privilege, SSRF, resource
  abuse, or supplying poisoned content (see [./ThreatModel.md](./ThreatModel.md),
  [./AIThreatModel.md](./AIThreatModel.md)).

## 2. Controls

1. **Signing & verification:** plugins are signed; signature verified before install.
2. **Manifest & least privilege:** declared capabilities, permissions, and egress needs;
   nothing beyond the manifest is granted.
3. **Sandboxing (DECIDED — [../adr/ADR-0013-plugin-sandbox.md](../adr/ADR-0013-plugin-sandbox.md)):**
   an out-of-process worker with **host-brokered capabilities** (no ambient network — the plugin
   cannot open a socket; all egress goes through the host) as the portable, air-gapped-capable
   baseline, reinforced by a rootless container (gVisor/Kata) in orchestrated profiles; non-root,
   read-only FS, resource limits. The isolation boundary is a pluggable sandbox-runner.
4. **Egress control:** default-deny network; explicit allowlist per plugin; blocks SSRF.
5. **Scoped credentials:** external-system creds from Vault, injected at runtime, never
   logged or exposed to other plugins.
6. **Untrusted output:** plugin/connector output treated as untrusted evidence.
7. **Audit & monitoring:** all plugin actions audited; anomalies alerted.

## 3. Lifecycle Security

- Install → verify → validate manifest → grant scoped perms → enable → monitor →
  upgrade/disable/remove ([../14-Plugins/PluginLifecycle.md](../14-Plugins/PluginLifecycle.md)).

## 4. Air-Gapped

- Plugins ship in the offline bundle; external-egress plugins are inert unless an internal
  endpoint is configured — preserving the no-egress guarantee.

## 5. Review

- First-party and marketplace plugins undergo security review before publication; a revoke
  mechanism disables compromised plugins fleet-wide.
