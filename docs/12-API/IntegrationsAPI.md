---
title: Integrations API (Plugins, Connectors)
document_id: API-007
status: Draft
version: 0.1.0
last_updated: 2026-08-13
owner: Integrations / Backend
audience: Developer, API consumer
phase: Phase 07 — Integrations (M007)
related:
  - ./Authentication.md
  - ./Authorization.md
  - ./AgentsAPI.md
  - ../14-Plugins/PluginImplementation.md
  - ../03-Architecture/IntegrationArchitecture.md
  - ../17-User-Documentation/IntegrationsUserGuide.md
---

# Integrations API

> **Purpose.** HTTP surface for the plugin/connector framework on the AI Gateway: list installed
> plugins, enable/disable them, and invoke **read** connector capabilities. Design and guarantees:
> [../14-Plugins/PluginImplementation.md](../14-Plugins/PluginImplementation.md). **Status:
> CURRENT** (offline profile).

All endpoints require a valid bearer token ([Authentication.md](./Authentication.md)) and are
authorized per-action via OPA ([Authorization.md](./Authorization.md)); calls are tenant-scoped.

## Endpoints

| Method & path | OPA action | Description |
|---------------|-----------|-------------|
| `GET /api/v1/plugins` | `plugins.read` | List installed plugins + capabilities + state |
| `POST /api/v1/plugins/{id}/enable` | `plugins.admin` | Enable a plugin (admin) |
| `POST /api/v1/plugins/{id}/disable` | `plugins.admin` | Disable a plugin (admin) |
| `POST /api/v1/connectors/{capability}/invoke` | `connectors.invoke` **+** the capability's own permission | Invoke a **read** connector capability |

The plugin host additionally authorizes each capability's own permission
(`connector.siem.search`, `connector.ti.lookup`, `connector.ti.live_lookup`, …). **Consequential**
capabilities (e.g. `ticketing.create_ticket`) are **not** invokable here — they must run through an
agent so they are human-approval-gated ([AgentsAPI.md](./AgentsAPI.md)).

## List plugins

```json
GET /api/v1/plugins  →
[
  {"id": "dula-plugin-dula-siem", "version": "0.1.0", "state": "enabled", "description": "…",
   "capabilities": [{"name": "siem.search", "side_effect": "read",
                     "permission": "connector.siem.search", "requires_egress": false}]}
]
```

## Invoke a read connector

```json
POST /api/v1/connectors/siem.search/invoke
{ "args": { "query": "HOST-7", "limit": 10 } }
```

Response (`InvokeResponse`): `{ "ok": true, "output": {…normalized…}, "error": null,
"untrusted": true }`. Errors: unknown capability → **404**; a **consequential** capability →
**409** (use an agent); endpoint authZ failure → **403**; per-capability authZ failure → **403**.

- `ti.live_lookup` requires egress; in an **air-gapped** install it returns `{"ok": false,
  "error": "egress denied: …"}` (inert, not an error status).

## Security guarantees

Plugins are verified (Ed25519 signature) before install, granted only manifest-declared
permissions, egress-restricted (default-deny allowlist + SSRF protection), resource-limited, and
their output is untrusted. See
[../14-Plugins/PluginImplementation.md](../14-Plugins/PluginImplementation.md) and
[../10-Security/PluginSecurity.md](../10-Security/PluginSecurity.md).
