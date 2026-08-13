---
title: Kubernetes Deployment
document_id: DEP-003
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Platform / Ops
audience: Platform & ops engineers
phase: Documentation Bootstrap (M000)
related:
  - ../03-Architecture/DeploymentArchitecture.md
  - ./CloudDeployment.md
  - ./OnPremDeployment.md
---

# Kubernetes Deployment

> **Purpose.** Define the production baseline: Helm-packaged deployment on Kubernetes,
> portable across cloud/on-prem/air-gapped via values overlays.
>
> **Delivered (Phase 09, CURRENT):** the umbrella chart lives at `deploy/helm/dula/` with
> per-profile overlays (`values-{cloud,onprem,hybrid,airgapped}.yaml`); admission policies at
> `deploy/kyverno/`. Validate: `helm lint deploy/helm/dula` and
> `helm template dula deploy/helm/dula -f deploy/helm/dula/values-<profile>.yaml`. Live cluster
> deploy + acceptance is operational — see [GAReadiness.md](./GAReadiness.md).

## 1. Packaging

- Umbrella Helm chart composing all components; per-profile **values** overlays.
- Signed images referenced by digest; GitOps via **Argo CD**.

## 2. Topology

See [../03-Architecture/DeploymentArchitecture.md](../03-Architecture/DeploymentArchitecture.md).
Stateless services (HPA autoscaled), stateful data services (operators/StatefulSets),
GPU-aware model serving pools.

## 3. Networking & Security

- **Envoy Gateway (Kubernetes Gateway API)** terminates TLS at the edge (ADR-0014); internal
  mTLS; **NetworkPolicies** segment planes; **default-deny egress** with explicit allowlists
  per profile.
- Admission control verifies image signatures/provenance via **Kyverno** (ADR-0015): only
  cosign-signed, attested images (verified against a mirrored public key) run, and the
  pod-security baseline is enforced (non-root, read-only rootfs, dropped caps, resource limits).

## 4. Configuration & Secrets

- Helm values + startup validation; secrets via Vault (CSI/agent) or SOPS-encrypted;
  never plaintext in manifests.

## 5. Scaling

- HPA on services; independent scaling of model-serving pools (GPU); data tier scaled per
  operator guidance. Load testing: [../15-Testing/PerformanceTesting.md](../15-Testing/PerformanceTesting.md).

## 6. Upgrades

- Rolling updates; forward-only DB migrations
  ([../07-Database/MigrationStrategy.md](../07-Database/MigrationStrategy.md)); canary for
  models ([../09-MLOps/DeploymentPipelines.md](../09-MLOps/DeploymentPipelines.md)).

## 7. Observability

- OTel + Prometheus/Grafana/Loki/Tempo deployed with the platform
  ([../16-Operations/Observability.md](../16-Operations/Observability.md)).

## 8. Backup/DR

- [../16-Operations/BackupRecovery.md](../16-Operations/BackupRecovery.md),
  [./DisasterRecovery.md](./DisasterRecovery.md).

## 9. Requirements

- Cluster version, GPU operator (if GPU), storage classes, and ingress controller are
  specified per install (**REQUIRES RESEARCH** for exact minimums).
