---
title: Milestone Closure — M007 (Phase 07 Integrations) — Complete
document_id: MVP-M007-CLOSURE
status: Reviewed
version: 1.0.0
last_updated: 2026-08-13
owner: Engineering
audience: Project Maintainer, Developer, Architect, Security Engineer, Integration Engineer, DevOps/SRE
phase: Phase 07 — Integrations (M007)
related:
  - ../Phase07-Integrations.md
  - ../../14-Plugins/PluginImplementation.md
  - ../../12-API/IntegrationsAPI.md
  - ../../17-User-Documentation/IntegrationsUserGuide.md
  - ../../10-Security/PluginSecurity.md
  - ../../PROJECT_STATE.md
  - ./README.md
---

# Milestone Closure — M007 (Phase 07 Integrations)

> Produced per **CLAUDE.md §11.8**. **This milestone is COMPLETE.** The plugin/connector
> framework (signing, manifest/permission model, egress allowlist + SSRF, host lifecycle), the
> first connectors, the plugins/connectors API and UI, and the agent→connector bridge are
> delivered; sandbox-policy/egress/air-gapped tests pass; technical + user documentation are done.

- **Milestone identifier:** M007
- **Milestone name:** Phase 07 — Integrations
- **Objective:** Deliver the plugin host + SDK + manifest/permission model and the first
  connectors (read search/lookup + one consequential), with normalization, sandboxing controls,
  egress allowlist, and contract tests (no live calls). See
  [../Phase07-Integrations.md](../Phase07-Integrations.md).

## Implemented functionality
- **Framework** (`packages/dula-plugins`): `manifest` (signed contract: id/version/publisher key/
  capabilities/egress/limits), `signing` (Ed25519 sign/verify + `TrustStore` with revocation),
  `egress` (default-deny allowlist + SSRF guard; disabled air-gapped), `connector` + `sdk`
  (contracts, `BaseConnector`, untrusted output, output-size limit), `host` (install→enable→
  disable→revoke; invoke enforces enabled→OPA permission→scoped egress+timeout→untrusted result;
  audited), `builtin` (sign+install+enable offline).
- **Connectors**: `siem.search` (read, normalized events), `ti.lookup_indicator` (read, offline
  reputation + IOC extraction) + `ti.live_lookup` (read, egress-gated), `ticketing.create_ticket`
  (consequential, idempotent).
- **API** (`apps/ai-gateway`): `GET /api/v1/plugins`, enable/disable, `POST /api/v1/connectors/
  {capability}/invoke` (read only; consequential → 409).
- **Agent→connector bridge**: the investigation agent's `search_logs` and `create_ticket` tools
  are backed by the SIEM and ticketing connectors (the consequential ticket stays approval-gated
  by the agent runtime).
- **UI** (`apps/web`): an **Integrations** page (list plugins/capabilities; invoke read
  connectors), nav-linked.

## Technical changes
- New workspace package `packages/dula-plugins` (offline; declares `cryptography` for Ed25519).
- `apps/ai-gateway`: `plugins_wiring.py` (OPA checker, demo backends, subsystem builder),
  `routers/plugins.py` (+ registration), `deps.py` accessor, `config.py` `plugins_egress_enabled`;
  `agents_wiring.py` now backs agent tools with connectors; added `dula-plugins` dependency.
- `apps/web`: `app/integrations/page.tsx` + `components/IntegrationsConsole.tsx` + `app/api/plugins`
  + `app/api/connectors/[capability]/invoke` proxy routes; `Nav.tsx` **Integrations** link.
- Root `pyproject.toml`: `dula-plugins` workspace member + source.

## Architecture changes
- No new infrastructure. Realises the plugin architecture (ARC-009) and integration architecture
  (inbound ingestion/enrichment + gated outbound). New product dependency **cryptography**
  (Apache-2.0/BSD, permissive; already transitively present via `pyjwt[crypto]`) for Ed25519
  signing. Reuses OPA (ADR-0009) + tenant isolation (ADR-0006). The **sandbox isolation mechanism
  is DECIDED ([ADR-0013](../../adr/ADR-0013-plugin-sandbox.md), recorded at close-out)** — an
  out-of-process worker with host-brokered capabilities (baseline) + container per profile, behind
  a pluggable runner; the framework's policy controls hold regardless of runner, and the in-process
  runner seam is delivered (OS-level runners FUTURE).

## Database changes
- None. The plugin registry + run/secret state are in-memory (durable registry + Vault FUTURE).

## API changes
- Added `/api/v1/plugins` (+ enable/disable) and `/api/v1/connectors/{capability}/invoke`
  ([../../12-API/IntegrationsAPI.md](../../12-API/IntegrationsAPI.md)). New OPA actions:
  `plugins.read`, `plugins.admin` (admin-only), `connectors.invoke`, and per-capability
  `connector.siem.search`/`connector.ti.lookup`/`connector.ti.live_lookup` (read → operational
  personas) + `connector.ticketing.create` (consequential → role-gated).

## Security changes / validation performed
- **Signed plugins** (Ed25519): verify-on-install; untrusted key, tampered manifest, and malformed
  signature all rejected; publisher **revocation** removes trust.
- **Least privilege**: only manifest-declared capabilities/permissions are granted; every call is
  OPA-authorized; **consequential** capabilities cannot be invoked directly (agent + approval).
- **Egress default-deny + SSRF**: only allowlisted https hosts; private/loopback/link-local/
  unresolvable blocked; **air-gapped** → egress disabled, egress-gated connectors **inert** (no
  phone-home) while offline connectors still work.
- **Untrusted output**, **resource limits** (timeout + output size), and **audit** on every call.

## AI/ML changes
- None (deterministic framework). The TI connector reuses the Phase 05 intel core for offline
  enrichment.

## Testing performed
- `ruff` + `ruff format --check` clean; `mypy --strict` clean (**103 source files**); **199 pytest
  pass, 5 skipped** (live-backend only), up from 157 — **+31** package tests (manifest/signing/
  egress/host/connectors/air-gapped) and **+11** API tests (endpoints, per-capability authz,
  consequential-blocked, agent→connector bridge, air-gapped inertness). OPA policy extended.
- `apps/web`: eslint clean, `tsc --noEmit` clean, `next build` succeeds with `/integrations` + the
  two proxy routes.
- **No live external calls in CI** — connectors are fixture-backed; the egress guard's SSRF path is
  unit-tested with loopback/unresolvable hosts.

## Deployment validation
- No new services/infrastructure; endpoints run in the existing `apps/ai-gateway` (offline profile
  verified via the test app). Air-gapped default (egress off) verified by tests.

## Documentation completed

### Documentation Impact Assessment (CLAUDE.md §11.6)
1. **Implemented:** plugin/connector framework + connectors + `/api/v1/plugins` + `/connectors/*`
   + agent bridge + Integrations UI.
2. **Technical docs created:** [../../14-Plugins/PluginImplementation.md](../../14-Plugins/PluginImplementation.md), [../../12-API/IntegrationsAPI.md](../../12-API/IntegrationsAPI.md); this closure; Phase 07 Completion Review.
3. **Technical docs updated:** 14-Plugins README (→CURRENT), 12-API README, SUMMARY, Glossary, PROJECT_STATE, PROJECT_CONTEXT, closure README.
4. **User docs created:** [../../17-User-Documentation/IntegrationsUserGuide.md](../../17-User-Documentation/IntegrationsUserGuide.md).
5. **User docs updated:** User-Documentation README index.
6. **Intentionally not created (N/A):** Database/Migration (no schema), Model card (no training), DR/Backup (in-memory MVP). (The sandbox mechanism was **decided at close-out** — see ADR-0013; a full sandbox-runtime enforcement doc lands with the OS-level worker runners.)
7. **Examples/commands verified:** endpoint request/response shapes exercised by integration tests.
8. **Links valid:** relative-link check passes. 9. **Diagrams:** existing plugin/integration diagrams remain accurate. 10-11. **Incomplete/gaps:** none blocking; the sandbox mechanism is decided (ADR-0013), with real HTTP connectors, third-party loader, and the OS-level sandbox runners FUTURE, not M007 gaps.

### Milestone Documentation Checklist (CLAUDE.md §11.7)
#### Technical
- [x] Architecture updated (implementation doc) · [x] API documentation updated · [N/A] Database
- [x] Configuration (OPA actions + egress flag) · [x] Security documentation referenced/consistent · [N/A] Deployment (no change)
- [x] Testing documentation updated · [~] Troubleshooting (user-guide "Good to know")
- [N/A] Operational/Runbook (stateless MVP) · [N/A] AI/ML · [N/A] RAG/Agent · [x] Plugin/integration documentation updated
#### User
- [x] Getting Started / Feature docs (Integrations User Guide) · [x] User guide updated
- [~] Administrator guide (enable/disable/revoke notes in the guide) · [x] Troubleshooting notes · [N/A] FAQ
#### Quality
- [x] Front matter · [x] Naming conventions · [x] Relative links validated
- [x] Commands/examples verified · [x] No undocumented functionality · [x] No FUTURE-as-CURRENT
- [x] SUMMARY updated · [x] Glossary terms added · [x] PROJECT_CONTEXT/STATE updated

## Known limitations
- **Sandbox mechanism DECIDED post-closure — [ADR-0013](../../adr/ADR-0013-plugin-sandbox.md)**
  (out-of-process worker + host-brokered capabilities baseline; container per orchestrated
  profile; pluggable `SandboxRunner`). The in-process runner is delivered; the **OS-level
  worker/container runners** are FUTURE. Today's isolation is the policy layer (signing,
  permissions, egress, limits, untrusted output, revocation) plus the runner seam.
- Connectors are **fixture-backed**; real SIEM/EDR/TI HTTP clients (via the egress guard) and a
  third-party plugin **loader** are FUTURE.
- The plugin registry + secrets are **in-memory** (durable registry + Vault-backed secrets FUTURE).

## Known issues
- None outstanding.

## Deferred work
- Sandbox runtime **enforcement** (the OS-level subprocess/container runners per ADR-0013; the
  decision + runner seam are done); real connector HTTP clients; third-party plugin loader +
  marketplace review; durable registry + Vault secrets; OCSF/ECS normalization; STIX/TAXII feed
  connector; connector rate-limiting/circuit-breakers.

## Lessons learned
- Separating the **policy controls** (signing, permissions, egress, limits, untrusted output,
  revocation) from the **isolation mechanism** let Phase 07 ship real, tested safety guarantees
  before committing to a sandbox mechanism — and that separation directly shaped the mechanism
  **decision (ADR-0013)**: a pluggable runner where the out-of-process worker + host-brokered
  capabilities reinforce controls that already hold. Backing agent tools with connectors kept the
  agent runtime as the single authorization/approval boundary, avoiding a second surface.

## Next milestone
- **Phase 08 — Automation** (security workflows/playbooks composing agents + connectors) on
  explicit go-ahead. Not started.

## Documentation gaps
- None blocking. Sandbox-runtime, real-connector, and loader docs land with those features.

## Final status
- **COMPLETE** — implementation + tests + security validation (signing/egress/SSRF/air-gapped) +
  technical *and* user documentation delivered and verified.
