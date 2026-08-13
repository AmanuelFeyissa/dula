---
title: Plugin Framework Implementation
document_id: PLG-005
status: Draft
version: 0.1.0
last_updated: 2026-08-13
owner: Integrations / Security
audience: Developer, Integration Engineer, Security Engineer
phase: Phase 07 — Integrations (M007)
related:
  - ./PluginFramework.md
  - ./PluginLifecycle.md
  - ./ConnectorStandards.md
  - ./PluginSecurity.md
  - ../03-Architecture/PluginArchitecture.md
  - ../03-Architecture/IntegrationArchitecture.md
  - ../10-Security/PluginSecurity.md
  - ../12-API/IntegrationsAPI.md
  - ../17-User-Documentation/IntegrationsUserGuide.md
---

# Plugin Framework Implementation

> **Purpose.** Technical reference for the Phase 07 plugin/connector framework delivered in
> **`packages/dula-plugins/`** and exposed by **`apps/ai-gateway`**. Realises the design in the
> other `14-Plugins/` docs and [PluginArchitecture.md](../03-Architecture/PluginArchitecture.md).
> **Status: CURRENT** (offline profile; process/WASM sandbox mechanism still REQUIRES DECISION).
> User guide: [../17-User-Documentation/IntegrationsUserGuide.md](../17-User-Documentation/IntegrationsUserGuide.md).

## Design stance

Plugins are **untrusted by default — even first-party** (PluginSecurity.md §2). The host enforces
the security **policy** controls regardless of authorship: an Ed25519 **signature** is verified
before install; only **manifest-declared** capabilities/permissions are granted; every capability
call is **OPA-authorized**; network egress is **default-deny** against the manifest allowlist with
**SSRF** protection; resource **limits** apply; and connector output is **untrusted evidence**.
Everything runs **offline** — built-in connectors are fixture-backed so contract tests need no
live calls, and any egress-requiring capability is **inert air-gapped** (no phone-home). The
process/container/WASM isolation boundary is deferred (REQUIRES DECISION); this framework provides
the controls it will reinforce.

## Components (`dula_plugins`)

| Module | Responsibility |
|--------|----------------|
| `manifest` | `PluginManifest` (id `dula-plugin-<vendor>-<product>`, version, publisher key, capabilities, egress allowlist, limits) + `Capability` (name `<system>.<capability>`, `SideEffect`, permission, `requires_egress`). `canonical_bytes()` is the signed representation. |
| `signing` | Ed25519 `sign_manifest`/`verify_plugin`, a `TrustStore` (trust/revoke by `publisher_key_id`). Fails closed on untrusted key, tamper, or malformed signature. |
| `egress` | `EgressGuard` + `EgressPolicy`: default-deny allowlist, https-only, SSRF block (private/loopback/link-local/unresolvable), globally disabled when air-gapped. |
| `connector` | `Connector` protocol, `ConnectorContext` (tenant/subject + egress guard + scoped `SecretProvider`), `ConnectorResult` (`untrusted=True`). |
| `sdk` | `BaseConnector`: dispatch by capability, reject undeclared capabilities, enforce the manifest output-size limit. |
| `host` | `PluginHost`: **install** (verify signature) → **enable** → **disable/revoke** (terminal); **invoke** enforces enabled → OPA permission → scoped egress + timeout → untrusted result; audited. |
| `connectors/` | Built-in `siem.search` (read), `ti.lookup_indicator` (read, offline) + `ti.live_lookup` (read, egress-gated), `ticketing.create_ticket` (consequential). |
| `builtin` | Signs + installs + enables the built-ins on an offline host (egress disabled by default). |

## Lifecycle & invocation

Install verifies the Ed25519 signature against the trust store (the **Verify** gate,
PluginLifecycle.md §2); enable makes capabilities invokable; **revoke** is a terminal fleet-wide
kill. On `invoke`, the host checks the plugin is enabled, authorizes the capability's permission
via OPA (**agent/user never self-grants**), builds a `ConnectorContext` with a scoped egress guard
(allowlist = manifest egress; disabled when air-gapped), runs the connector under a timeout, and
returns the result as untrusted. Every step is audited.

## Normalization

Connectors normalize external data to internal shapes (IntegrationArchitecture.md §2): e.g.
`siem.search` returns `{count, events:[{ts,host,message,source}]}`; `ti.lookup_indicator` returns
`{indicators:[{kind,value,reputation,sources}]}`. Prefer open standards (STIX/TAXII, Sigma, YARA)
for real feeds.

## Agent → connector bridge

`apps/ai-gateway` backs the investigation agent's `search_logs` and `create_ticket` tools with the
SIEM and ticketing **connectors** (agent→connector). Authorization for those calls remains the
**agent runtime's** responsibility (it OPA-checks the tool before calling), and the consequential
ticket stays **human-approval-gated** by the runtime — the connector is the execution path, not a
second authorization surface.

## API surface

`apps/ai-gateway` exposes `/api/v1/plugins` (list; `plugins.read`), enable/disable
(`plugins.admin`), and `/api/v1/connectors/{capability}/invoke` (`connectors.invoke` + the
capability's own permission). **Consequential** capabilities are not directly invokable — they run
through an agent (approval-gated). Contract:
[../12-API/IntegrationsAPI.md](../12-API/IntegrationsAPI.md). `apps/web` adds an **Integrations**
page.

## Evaluation & security tests

`packages/dula-plugins/tests/` — signing/tamper/trust-revocation, egress allowlist + SSRF,
host lifecycle + permission enforcement, connector contracts (fixtures, no live calls), and
**air-gapped inertness** (egress-gated capability fails closed; offline capability works).
`apps/ai-gateway/tests/test_plugins.py` covers the endpoints, per-capability authz, the
consequential-blocked-direct rule, and the agent→connector bridge.

## Maturity & limits

- **Sandbox mechanism REQUIRES DECISION** (process/container/WASM). Today isolation is the
  policy layer (signing, permissions, egress, limits, untrusted output, revocation); a runtime
  boundary is FUTURE.
- Built-in connectors are **fixture-backed**; real SIEM/EDR/TI HTTP clients (via the egress guard)
  and a third-party plugin loader are FUTURE.
- The plugin registry + secrets are in-memory; durable registry + Vault-backed secrets are FUTURE.
