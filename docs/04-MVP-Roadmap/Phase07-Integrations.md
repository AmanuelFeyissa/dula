---
title: Phase 07 — Integrations
document_id: MVP-007
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Integrations / Security
audience: All contributors
phase: Documentation Bootstrap (M000)
related:
  - ../03-Architecture/PluginArchitecture.md
  - ../14-Plugins/README.md
---

# Phase 07 — Integrations

> **Purpose.** Connect Dula to the external security ecosystem via the sandboxed
> plugin/connector framework.

## Objective
Deliver the plugin host + SDK and the first connectors (e.g. a SIEM search, a TI lookup),
enabling ingestion, enrichment, and (gated) outbound actions.

## Scope
- Plugin host + SDK + manifest/permission model
  ([../14-Plugins/PluginFramework.md](../14-Plugins/PluginFramework.md)); sandbox mechanism
  **decided ([../adr/ADR-0013-plugin-sandbox.md](../adr/ADR-0013-plugin-sandbox.md))**.
- First connectors ([../14-Plugins/ConnectorStandards.md](../14-Plugins/ConnectorStandards.md)):
  read (search/lookup) + one consequential (e.g. create ticket) behind approval.
- Normalization of external data to the internal schema (see [../03-Architecture/IntegrationArchitecture.md](../03-Architecture/IntegrationArchitecture.md)).

## Dependencies
- Phase 06 (agents can use connector tools); core data model stable.

## Deliverables
- Install/enable a signed plugin; ingest/enrich from an external system; agent uses a
  connector tool; outbound action requires approval.

## Implementation Requirements
- Sandboxing + egress allowlist + scoped secrets
  ([../10-Security/PluginSecurity.md](../10-Security/PluginSecurity.md)); contract tests
  with fixtures (no live calls in CI).

## Tests
- Connector contract tests; sandbox-escape & egress-bypass tests; SSRF checks
  ([../15-Testing/SecurityTesting.md](../15-Testing/SecurityTesting.md)).

## Security Requirements
- Signed plugins; least-privilege; default-deny egress; untrusted output; revocation path.

## Documentation
- Plugin dev guide; connector docs; update PROJECT_STATE.

## Acceptance Criteria
- A signed connector ingests and enriches data safely; sandbox/egress tests pass;
  air-gapped behavior (external plugins inert) verified.

## Definition of Done
- Global DoD + above.
