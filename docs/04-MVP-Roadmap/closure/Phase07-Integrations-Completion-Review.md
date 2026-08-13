---
title: Phase Completion Review — Phase 07 (Integrations)
document_id: MVP-P07-COMPLETION
status: Reviewed
version: 1.0.0
last_updated: 2026-08-13
owner: Engineering
audience: Project Maintainer, Architect, Developer, Security Engineer, Integration Engineer, DevOps/SRE
phase: Phase 07 — Integrations
related:
  - ../Phase07-Integrations.md
  - ./M007-Integrations-Closure.md
  - ../../14-Plugins/PluginImplementation.md
  - ../../PROJECT_STATE.md
---

# Phase Completion Review — Phase 07 (Integrations)

> Produced per **CLAUDE.md §11.9**. Phase 07 contains one milestone (M007); its
> [closure report](./M007-Integrations-Closure.md) holds the detailed §11.6/§11.7 assessment.

## Phase objective
Connect Dula to the external security ecosystem via a **sandboxed plugin/connector framework**:
deliver the plugin host + SDK + manifest/permission model and the first connectors (read
search/lookup + one consequential), safely and portably (incl. air-gapped).

## Milestones completed
- **M007 — Integrations:** COMPLETE ([M007 closure](./M007-Integrations-Closure.md)).

## Features / capability delivered
- **Framework** (`packages/dula-plugins`): Ed25519 manifest signing + trust/revocation; default-deny
  egress allowlist + SSRF guard; a host (install→enable→disable→revoke, OPA-authorized invoke with
  limits + audit + untrusted output); a connector SDK.
- **Connectors**: `siem.search`, `ti.lookup_indicator` (+ egress-gated `ti.live_lookup`),
  `ticketing.create_ticket` (consequential) — normalized, offline-capable.
- **API**: `/api/v1/plugins` (+ enable/disable) and `/api/v1/connectors/{capability}/invoke`.
- **Agent→connector bridge**: the investigation agent's `search_logs`/`create_ticket` tools are
  connector-backed; the ticket stays approval-gated.
- **UI**: an `apps/web` **Integrations** page.

## Architecture delivered
Realises the plugin (ARC-009) and integration architectures. New product dependency
**cryptography** (permissive; already transitively present) for Ed25519. Reuses OPA (ADR-0009) +
tenant isolation (ADR-0006). The **sandbox isolation mechanism (process/WASM) remains REQUIRES
DECISION**; the framework enforces the policy controls it will reinforce, so the security
guarantees are real now and a runtime boundary strengthens them later.

## Security posture
Plugins are untrusted-by-default: signature-verified on install; granted only manifest-declared
permissions; every capability call OPA-authorized; egress default-deny with SSRF protection;
resource-limited; output untrusted; consequential capabilities routed through agents (approval).
Air-gapped-first: egress disabled by default, egress-gated connectors inert with no phone-home.
Aligns with [../../10-Security/PluginSecurity.md](../../10-Security/PluginSecurity.md).

## Testing status
`ruff`/`ruff format`/`mypy --strict` clean (103 files); **199 pytest pass, 5 skipped** — +31
package tests and +11 API tests over Phase 06. OPA policy tests extended. `apps/web` eslint/`tsc
--noEmit`/`next build` clean, including `/integrations`. No live external calls in CI (fixtures +
unit-tested SSRF path).

## Documentation status
Created the [Plugin Framework Implementation](../../14-Plugins/PluginImplementation.md) and
[Integrations API](../../12-API/IntegrationsAPI.md) docs; set 14-Plugins status to CURRENT;
updated the 12-API README, SUMMARY, Glossary, PROJECT_STATE, PROJECT_CONTEXT, and closure README;
links validated.

## User-documentation status
Created the [Integrations User Guide](../../17-User-Documentation/IntegrationsUserGuide.md) (view
connectors; run read lookups; admin enable/disable/revoke); User-Documentation README index
updated.

## Known limitations / technical debt / deferred
- **Sandbox mechanism REQUIRES DECISION** (process/container/WASM) — isolation is the policy layer today.
- Connectors are fixture-backed; real HTTP clients (via the egress guard), a third-party plugin
  loader + marketplace review, durable registry, and Vault-backed secrets are FUTURE.
- OCSF/ECS normalization and a STIX/TAXII feed connector are deferred.

## Outstanding risks
None blocking. The policy controls (signing, permissions, egress, limits, untrusted output,
revocation) are enforced regardless of the isolation mechanism, so adopting a process/WASM sandbox
later strengthens — not replaces — the guarantees; tests guard against regressions.

## Next-phase prerequisites
Phase 08 (Automation) composes agents + connectors into workflows/playbooks; the runtime,
permission/approval flow, and connector framework are in place. Not started; begins on explicit
go-ahead.

## Phase status
**Phase 07 — COMPLETE.** Implementation, tests, security validation (signing/egress/SSRF/
air-gapped), and technical *and* user documentation are done and verified. Awaiting go-ahead for
Phase 08.
