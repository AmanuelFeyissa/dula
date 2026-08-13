---
title: Milestone Closure — M009 (Phase 09 Production) — Complete (GA sign-off operational)
document_id: MVP-M009-CLOSURE
status: Reviewed
version: 1.0.0
last_updated: 2026-08-13
owner: Engineering
audience: Project Maintainer, Developer, Architect, Security Engineer, DevOps/SRE
phase: Phase 09 — Production (M009)
related:
  - ../Phase09-Production.md
  - ../../11-Deployment/GAReadiness.md
  - ../../11-Deployment/KubernetesDeployment.md
  - ../../10-Security/SupplyChainSecurity.md
  - ../../17-User-Documentation/InstallationGuide.md
  - ../../adr/ADR-0014-edge-gateway.md
  - ../../adr/ADR-0015-supply-chain-release-integrity.md
  - ../../PROJECT_STATE.md
  - ./README.md
---

# Milestone Closure — M009 (Phase 09 Production)

> Produced per **CLAUDE.md §11.8**. **This milestone is COMPLETE for its buildable scope** — the
> production-readiness **artifacts, automation, and policies** plus technical *and* user docs are
> delivered and verified in CI. **GA is NOT declared:** the live multi-profile deploy, external
> penetration test, and DR restore drill require real infrastructure/an external party and are
> **operational** items tracked in [GAReadiness.md](../../11-Deployment/GAReadiness.md). Nothing
> live was claimed as done.

- **Milestone identifier:** M009
- **Milestone name:** Phase 09 — Production (GA)
- **Objective:** Production hardening across all profiles (incl. air-gapped): a signed, reproducible,
  profile-portable release, supply-chain integrity, observability/SLOs, backup/DR, and security
  hardening ([../Phase09-Production.md](../Phase09-Production.md)).

## Decisions resolved (I owned these per the delegation)
- **ADR-0014 — Edge / API gateway:** Envoy Gateway (Kubernetes Gateway API) at the north-south
  edge; FastAPI services behind it; authz/authn stay first-party (OPA/Keycloak). Resolves the
  long-open "API gateway technology" item.
- **ADR-0015 — Supply-chain & release integrity:** cosign **keyed** signing (offline-verifiable) +
  syft SBOM + grype gate + **Kyverno** admission; **SLSA Build L3**; signed commits recommended,
  enforced on protected branches at GA. Resolves the "admission-control tool" and "SLSA level" items.

## Implemented functionality
- **Umbrella Helm chart** (`deploy/helm/dula`): DRY component model rendering hardened Deployments
  (non-root, read-only rootfs, dropped caps, seccomp, resource limits, probes, rolling update with
  `maxUnavailable: 0`), Services, HPA, PDB, default-deny **NetworkPolicies**, **Gateway API**
  Gateway/HTTPRoutes, a forward-only **pre-upgrade migration Job**, ServiceMonitor, ConfigMap,
  ServiceAccount — with per-profile overlays **cloud / on-prem / hybrid / air-gapped**.
- **Production Dockerfiles**: fixed `ai-gateway` (now copies the full workspace it depends on:
  dula-agents/plugins/automation) and added a hardened **web** image (Next.js standalone, non-root,
  no telemetry phone-home).
- **Supply chain**: `.github/workflows/release.yml` (build → syft SBOM → grype gate → cosign sign +
  attest, gated on tag/dispatch) and **Kyverno** policies (`deploy/kyverno/`: verify signatures +
  pod-security baseline).
- **Air-gapped**: offline image bundle (`deploy/airgap/images.txt` + `mirror-images.sh`) and a
  **no-egress assertion** (`verify-airgap.sh`) that passes in CI for the air-gapped overlay.
- **Observability**: Prometheus alert/recording rules + SLO targets + a Grafana dashboard
  (`deploy/observability/`).
- **Backup/DR**: checksum-verified Postgres backup/restore scripts (`deploy/backup/`) + DR runbook.
- **CI**: a new **`deploy`** job (helm lint + template for every profile + kubeconform + air-gap
  assertion + policy/observability YAML/JSON validation + shell syntax).

## Technical changes
- New `deploy/helm/`, `deploy/kyverno/`, `deploy/airgap/`, `deploy/observability/`, `deploy/backup/`.
- New `.github/workflows/release.yml`; new `deploy` job in `ci.yml`.
- `apps/ai-gateway/Dockerfile` fixed; `apps/web/Dockerfile` added.
- Helm chart cache mount aligned to the Next.js standalone layout.

## Architecture changes
- Realises the deployment architecture (ARC-003): one signed image + Helm chart per component,
  profiles as values overlays, air-gapped offline bundle. Two new ADRs (0014, 0015). No change to
  application code behaviour; edge/admission are infrastructure layers.

## Database changes
- None (schema unchanged). Migrations run as a forward-only pre-upgrade Helm hook.

## API changes
- None.

## Security changes / validation performed
- **Hardened runtime** enforced twice: the chart sets the security context, and **Kyverno** admits
  only pods that satisfy it — non-root, read-only rootfs, dropped caps, seccomp, resource limits.
- **Signed-image admission** (cosign keyed, offline-verifiable) blocks unsigned/unattested images.
- **Default-deny egress** NetworkPolicies per profile; air-gapped adds **no external egress** —
  asserted by `verify-airgap.sh` in CI.
- **Secrets** never inlined — referenced from an external Secret (Vault/SOPS).
- Existing gates unchanged (OPA authz, gitleaks, agent/plugin safety, red-team).

## Testing performed
- **`helm lint`** clean; **`helm template`** renders 26 manifests for **each** of the four profiles;
  **`kubeconform`** validates all built-in kinds (19 valid / 0 invalid; 7 CRDs — Gateway/HTTPRoute/
  ServiceMonitor — validated at deploy time). **Air-gap no-egress assertion passes.** Kyverno +
  observability YAML/JSON validated. Shell scripts pass `bash -n`.
- Existing suites unchanged: ruff/format/mypy-strict clean; **227 pytest** pass, 5 skipped; web
  eslint/tsc/build clean; docs link + naming checks pass.

## Deployment validation
- Everything verifiable **without** a live cluster is verified in CI (the `deploy` job). Live
  multi-profile deploy, admission enforcement behaviour, zero-downtime upgrade, air-gap enclave
  rehearsal, and the DR restore drill are **operational** (no cluster/registry/pen-test vendor in
  this environment) — tracked in [GAReadiness.md](../../11-Deployment/GAReadiness.md).
- A live Postgres backup/restore roundtrip was **not** run here (the local Docker engine was
  unavailable); the scripts are syntax-validated and use standard `pg_dump`/`pg_restore`.

## Documentation completed

### Documentation Impact Assessment (CLAUDE.md §11.6)
1. **Implemented:** Helm chart + overlays, Dockerfiles, Kyverno, air-gap tooling, observability,
   backup/DR, release + deploy CI.
2. **Technical docs created:** [ADR-0014](../../adr/ADR-0014-edge-gateway.md),
   [ADR-0015](../../adr/ADR-0015-supply-chain-release-integrity.md),
   [GAReadiness.md](../../11-Deployment/GAReadiness.md); this closure; Phase 09 review.
3. **Technical docs updated:** KubernetesDeployment, AirGappedDeployment, SupplyChainSecurity,
   Observability, BackupRecovery, deploy/README, ADR index + governance ADR table, TechnologyStack,
   CLAUDE.md §6, SUMMARY, Glossary, PROJECT_STATE, PROJECT_CONTEXT, roadmap Phase09, closure README.
4. **User docs created:** [InstallationGuide.md](../../17-User-Documentation/InstallationGuide.md).
5. **User docs updated:** User-Documentation README index (Installation → MVP).
6. **Intentionally not created (N/A):** Terraform/IaC (FUTURE), API/Database docs (no change),
   Model card (no training).
7. **Commands verified:** helm/kubeconform/airgap commands run locally. 8. **Links valid.**
   9. **Diagrams:** existing DeploymentArchitecture topology remains accurate. 10–11. **Gaps:** the
   application `/metrics` exporter and all operational GA items are FUTURE/operational, tracked in
   GAReadiness.md — not silent gaps.

### Milestone Documentation Checklist (CLAUDE.md §11.7)
#### Technical
- [x] Architecture (ADR-0014/0015) · [N/A] API · [N/A] Database (schema) · [x] Configuration (chart values)
- [x] Security (supply-chain/admission/netpol) · [x] Deployment (chart/profiles/air-gap) · [x] Testing (deploy CI)
- [x] Troubleshooting (install guide) · [x] Operational/Runbook (backup/DR, GA readiness) · [x] Monitoring/Observability
#### User
- [x] Installation guide · [x] Operator guide (install/upgrade/backup) · [~] Getting Started (root README interim)
- [x] Troubleshooting · [N/A] FAQ
#### Quality
- [x] Front matter · [x] Naming · [x] Relative links validated · [x] Commands verified
- [x] No undocumented functionality · [x] No FUTURE-as-CURRENT (operational items marked) · [x] SUMMARY updated
- [x] Glossary terms added · [x] PROJECT_CONTEXT/STATE updated

## Known limitations
- **GA not declared**: live 4-profile deploy, external pen test, and DR drill are operational.
- Application **`/metrics` exporter** is FUTURE (OTel stub today); request-level SLI rules attach then.
- **Terraform/IaC** for cloud/on-prem primitives is FUTURE.
- Kyverno signature verification uses a **placeholder** public key — replaced at install with the
  mirrored release key.

## Known issues
- None outstanding.

## Deferred work
- Live multi-profile deploy + acceptance; external penetration test; DR restore drill with RPO/RTO;
  full air-gap enclave rehearsal; the app Prometheus exporter; Terraform IaC; `kyverno test`/
  Chainsaw policy behaviour tests in CI; GitOps (Argo CD) app-of-apps.

## Lessons learned
- Making the deployment a **single chart with values overlays** (not per-profile forks) kept the
  air-gapped profile a *values* concern, so a CI no-egress assertion could prove the offline promise
  mechanically. Splitting **decision from enforcement** again paid off: the chart sets the hardened
  security context and Kyverno independently admits only pods that satisfy it — defence in depth that
  is verifiable before any cluster exists.

## Next milestone
- **Phase 10 — MLOps at scale** on explicit go-ahead. Not started.

## Documentation gaps
- None blocking. Live-deploy/pen-test/DR-drill evidence and the metrics-exporter docs land with
  those operational/FUTURE items.

## Final status
- **COMPLETE (buildable scope)** — production-readiness artifacts, automation, policies, and
  technical *and* user documentation delivered and verified in CI. **GA sign-off is pending the
  operational acceptance items** (live multi-profile deploy, pen test, DR drill) recorded in
  [GAReadiness.md](../../11-Deployment/GAReadiness.md).
