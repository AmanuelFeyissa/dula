---
title: GA Readiness Checklist
document_id: DEP-009
status: Draft
version: 0.1.0
last_updated: 2026-08-13
owner: Platform / Security / Ops
audience: Platform & ops engineers, Security Engineer, Project Maintainer
phase: Phase 09 — Production (M009)
related:
  - ./KubernetesDeployment.md
  - ./AirGappedDeployment.md
  - ./DisasterRecovery.md
  - ../10-Security/SupplyChainSecurity.md
  - ../16-Operations/Observability.md
  - ../04-MVP-Roadmap/Phase09-Production.md
  - ../adr/ADR-0014-edge-gateway.md
  - ../adr/ADR-0015-supply-chain-release-integrity.md
---

# GA Readiness Checklist

> **Purpose.** Honest, single-source status of production/GA readiness. Phase 09 delivers the
> **artifacts, automation, and policies** that make GA achievable and are **verifiable in CI**;
> items that require **live infrastructure or an external party** (a running cluster, a pen-test
> vendor, a real DR target) are marked **operational** and executed at deploy time. Nothing here
> is claimed done until it is actually done — a live 4-profile deploy and a pen test have **not**
> been performed in this repository.

## Legend
`[x]` delivered + verified here · `[~]` scaffolding delivered, completion is operational ·
`[ ]` operational (needs live infra / external party) — **not** done.

## Packaging & deployment
- [x] Umbrella **Helm chart** (`deploy/helm/dula`) — one chart, all profiles via values overlays.
- [x] Per-profile overlays: **cloud / on-prem / hybrid / air-gapped** (`values-*.yaml`).
- [x] Chart validated in CI: `helm lint` + `helm template` (every profile) + `kubeconform`.
- [x] Hardened workloads: non-root, read-only rootfs, dropped caps, seccomp, resource limits,
      probes, rolling update (`maxUnavailable: 0`), HPA, PDB.
- [x] **Edge** via Envoy Gateway / Gateway API (ADR-0014); TLS via cert-manager (values).
- [x] Forward-only **migration** as a pre-upgrade Helm hook (zero-downtime intent).
- [x] Production **Dockerfiles** for all four services (multi-stage, non-root; web standalone).
- [ ] **Identical release deployed + acceptance-passed on all four live profiles** (operational).
- [ ] Zero-downtime upgrade demonstrated on a live cluster (operational).

## Supply chain & release integrity (ADR-0015)
- [x] Decisions recorded: cosign **keyed** signing, syft SBOM, grype gate, **Kyverno** admission,
      **SLSA Build L3**, signed commits policy.
- [x] **Release pipeline** (`.github/workflows/release.yml`): build → SBOM → scan → sign (gated on
      tag/dispatch; signing/push run when release secrets are present).
- [x] **Kyverno** policies (`deploy/kyverno/`): verify-image-signatures + pod-security baseline.
- [~] Admission enforcement is validated at deploy time (`kyverno test`/Chainsaw); YAML validated in CI.
- [ ] External **penetration test**, no unresolved Critical/High (operational, external party).

## Air-gapped
- [x] Offline **image bundle** manifest + mirror/save/load script (`deploy/airgap/`).
- [x] **No-egress assertion** (`verify-airgap.sh`) — passes in CI for the air-gapped overlay.
- [x] Air-gapped values: no external egress, connector egress off, offline model path.
- [ ] Full offline install rehearsed end-to-end in a disconnected enclave (operational).

## Observability & SLOs
- [x] **SLO targets** defined (availability ≥ 99.5%, p95 < 800 ms) + Prometheus **alert/recording
      rules** + a Grafana dashboard (`deploy/observability/`).
- [x] `ServiceMonitor` scaffolding in the chart.
- [~] Application **/metrics exporter** — telemetry is an OTel stub today; the request-level SLI
      rules attach when the exporter lands (FUTURE, tracked).

## Backup / DR
- [x] Postgres **backup/restore** scripts with checksum (`deploy/backup/`); DR runbook + RPO/RTO.
- [ ] **DR restore drill** meeting RPO/RTO on a live target (operational).

## Security hardening
- [x] Default-deny **NetworkPolicies** with explicit allowlists; air-gapped = no external egress.
- [x] Secrets referenced from an external Secret (Vault/SOPS) — never inline in values.
- [x] Existing gates: OPA authz, gitleaks secret scan, agent/plugin safety suites, red-team tests.
- [ ] Full threat-model coverage re-verified against the live deployment (operational).

## Summary
Phase 09 makes GA **executable**: a signed, reproducible, profile-portable release with hardening,
admission, air-gap tooling, observability, and DR — all verified as far as a repository without a
live cluster can. **GA sign-off remains pending** the operational items above (live multi-profile
deploy, pen test, DR drill), which require real infrastructure and are owned by the deploying team.
