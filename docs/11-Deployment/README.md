---
title: Deployment — Overview
document_id: DEP-000
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Platform / Ops
audience: Platform & ops engineers
phase: Documentation Bootstrap (M000)
related:
  - ../03-Architecture/DeploymentArchitecture.md
---

# 11 — Deployment

> **Purpose.** How Dula is deployed and operated across profiles from one codebase.
> Architecture view: [../03-Architecture/DeploymentArchitecture.md](../03-Architecture/DeploymentArchitecture.md).

## Deployment Profiles

| Profile | Doc | Summary |
|---------|-----|---------|
| Local dev | [LocalDevelopment.md](./LocalDevelopment.md) | Docker Compose, small local models |
| Docker | [DockerDeployment.md](./DockerDeployment.md) | Compose for small single-host |
| Kubernetes | [KubernetesDeployment.md](./KubernetesDeployment.md) | Production baseline |
| Cloud | [CloudDeployment.md](./CloudDeployment.md) | K8s + optional managed services |
| On-prem | [OnPremDeployment.md](./OnPremDeployment.md) | Self-hosted K8s |
| Air-gapped | [AirGappedDeployment.md](./AirGappedDeployment.md) | Offline bundle, no egress |
| Hybrid | see CloudDeployment/OnPrem | Split control/data planes |
| DR | [DisasterRecovery.md](./DisasterRecovery.md) | Backup/restore, failover |
| GA readiness | [GAReadiness.md](./GAReadiness.md) | Honest production/GA status (Phase 09) |

> **Delivered (Phase 09):** the umbrella Helm chart (`deploy/helm/dula`) + per-profile overlays,
> admission policies (`deploy/kyverno`), air-gap bundle tooling (`deploy/airgap`), observability
> (`deploy/observability`), and backup/DR (`deploy/backup`). Edge = Envoy Gateway (ADR-0014);
> supply chain = ADR-0015. Operator how-to: [../17-User-Documentation/InstallationGuide.md](../17-User-Documentation/InstallationGuide.md).

## Profile Differences at a Glance

| Concern | Dev | Cloud | On-prem | Air-gapped |
|---------|-----|-------|---------|-----------|
| Orchestration | Compose | K8s | K8s | K8s |
| Data services | containers | managed optional | self-hosted | self-hosted |
| Models | small local | GPU vLLM | vLLM/llama.cpp | local only (bundle) |
| External egress | allowed | optional | optional | **none** |
| Secrets | .env (dev only) | Vault/KMS | Vault | on-prem Vault/KMS |

## Principle

**One codebase and chart set; profiles are values overlays, not forks.** A feature isn't
done until it works (or degrades gracefully) in air-gapped mode.
