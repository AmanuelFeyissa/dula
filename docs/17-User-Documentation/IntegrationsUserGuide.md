---
title: Integrations — User Guide (Plugins & Connectors)
document_id: USR-005
status: Draft
version: 0.1.0
last_updated: 2026-08-13
owner: Product / Docs
audience: End User, Operator, Administrator, Integration Engineer
phase: Phase 07 — Integrations (M007)
related:
  - ./README.md
  - ./AgentsUserGuide.md
  - ../12-API/IntegrationsAPI.md
  - ../14-Plugins/PluginImplementation.md
---

# Integrations — User Guide

> **Purpose.** How to view Dula's connectors to external security systems and run read lookups.
> **Status: MVP.** Technical reference:
> [../14-Plugins/PluginImplementation.md](../14-Plugins/PluginImplementation.md).

## What it does

Dula connects to external security systems (SIEM, threat-intel, ticketing) through **signed,
sandboxed connectors**. You can:

- **See** which connectors are installed and what each can do.
- **Run read lookups** on demand — search the SIEM, look up an indicator's reputation.
- Let the **investigation agent** use connectors for you (searching logs, and — with your
  approval — creating a ticket).

Safety, enforced by the platform:

- Each connector is **signature-verified** before it is installed, and granted only the
  permissions its manifest declares.
- Connectors reach the network only through a **default-deny allowlist** with SSRF protection; in
  an **air-gapped** install, connectors that need the internet are simply **inert** (no
  phone-home).
- **Consequential** actions (like creating a ticket) are never run directly — they go through an
  agent and require **your approval**.
- Connector output is treated as **untrusted** evidence.

## Using the Integrations page

1. Sign in and open **Integrations** in the top navigation.
2. Review the **installed plugins** and their capabilities (read vs consequential; whether they
   need egress).
3. Under **Invoke a read connector**, pick a capability (e.g. `siem.search` or
   `ti.lookup_indicator`), edit the JSON arguments, and select **Invoke**. The normalized result
   appears below.

## Using the API

```json
POST /api/v1/connectors/ti.lookup_indicator/invoke
{ "args": { "value": "evil.example.com" } }
```

Returns a normalized result (`{ "ok": true, "output": { "indicators": [ … ] } }`). List connectors
with `GET /api/v1/plugins`. Full contract: [../12-API/IntegrationsAPI.md](../12-API/IntegrationsAPI.md).

## Administration

- Enabling/disabling a plugin is **admin-only** (`POST /api/v1/plugins/{id}/enable|disable`).
- A compromised plugin can be **revoked** (fleet-wide disable) — a revoked plugin cannot be
  re-enabled.

## Good to know

- **Read-only here, consequential via agents.** Ticket creation and other consequential actions
  run through the [investigation agent](./AgentsUserGuide.md) with approval.
- **Air-gapped friendly.** Offline lookups (reputation, SIEM search over local data) work without
  the internet; live-feed lookups are inert until egress is configured.
- **Tenant-scoped and audited.** Every connector call is authorized, tenant-scoped, and logged.

## Getting help

- API reference: [../12-API/IntegrationsAPI.md](../12-API/IntegrationsAPI.md).
- Investigation agent: [./AgentsUserGuide.md](./AgentsUserGuide.md).
