---
title: Plugins — Overview
document_id: PLG-000
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Integrations / Security
audience: Integration & security engineers
phase: Documentation Bootstrap (M000)
---

# 14 — Plugins

> **Purpose.** The extensibility framework: sandboxed plugins providing connectors and
> tools for external security systems. **Status: FUTURE (Phase 07).**

## Documents

- [PluginFramework.md](./PluginFramework.md)
- [PluginLifecycle.md](./PluginLifecycle.md)
- [ConnectorStandards.md](./ConnectorStandards.md)
- [PluginSecurity.md](./PluginSecurity.md)

## Foundations

- Architecture: [../03-Architecture/PluginArchitecture.md](../03-Architecture/PluginArchitecture.md),
  [../03-Architecture/IntegrationArchitecture.md](../03-Architecture/IntegrationArchitecture.md).
- Security: [../10-Security/PluginSecurity.md](../10-Security/PluginSecurity.md).

## Principles

1. Sandboxed + least privilege + default-deny egress.
2. Signed + manifest-declared capabilities.
3. Output treated as untrusted evidence.
4. Works within air-gapped constraints (external-egress plugins inert offline).
