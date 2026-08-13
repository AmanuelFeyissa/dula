---
title: Installation & Operations Guide
document_id: USR-007
status: Draft
version: 0.1.0
last_updated: 2026-08-13
owner: Product / Docs / Ops
audience: Administrator, Operator, DevOps/SRE
phase: Phase 09 — Production (M009)
related:
  - ./README.md
  - ../11-Deployment/KubernetesDeployment.md
  - ../11-Deployment/AirGappedDeployment.md
  - ../11-Deployment/GAReadiness.md
  - ../10-Security/SupplyChainSecurity.md
---

# Installation & Operations Guide

> **Purpose.** How an operator installs and runs Dula on Kubernetes across profiles, using the
> umbrella Helm chart. **Status: MVP.** Technical reference:
> [../11-Deployment/KubernetesDeployment.md](../11-Deployment/KubernetesDeployment.md).

## What you install

Dula ships as one **Helm chart** (`deploy/helm/dula`) that deploys the web app, the platform API,
the AI gateway, and the worker — plus their networking, autoscaling, and security policies. The
same chart serves every environment; you pick a **profile** by choosing a values overlay. Data
services (Postgres, Qdrant, OpenSearch, Redpanda, Redis, MinIO) and platform services (Keycloak,
OPA, the Envoy Gateway, Kyverno) are installed alongside per your environment.

## Prerequisites

- A Kubernetes cluster (v1.27+) and `kubectl` + `helm`.
- The **Gateway API** CRDs + an **Envoy Gateway** controller (edge; ADR-0014).
- **Kyverno** installed (admission policies; ADR-0015).
- A **Secret** named `dula-secrets` (via Vault CSI or SOPS) holding `DATABASE_URL`, and any
  provider keys — never put secrets in values files.
- For air-gapped: a private registry populated from the offline bundle (see below).

## Install (choose a profile)

```bash
# Apply admission policies (once per cluster).
kubectl apply -f deploy/kyverno/

# Install Dula into a namespace, using a profile overlay.
helm upgrade --install dula deploy/helm/dula \
  --namespace dula-prod --create-namespace \
  -f deploy/helm/dula/values-cloud.yaml
```

Profiles: `values-cloud.yaml`, `values-onprem.yaml`, `values-hybrid.yaml`, `values-airgapped.yaml`.
Override the image tag with a signed digest for production: `--set global.imageTag=@sha256:...`.

## Air-gapped install

```bash
# Connected side: pull + save every image to a portable bundle.
deploy/airgap/mirror-images.sh save /media/usb/dula-bundle.tar

# Enclave side: load + push into the private mirror, then install with the air-gapped overlay.
deploy/airgap/mirror-images.sh load /media/usb/dula-bundle.tar
deploy/airgap/mirror-images.sh push registry.airgap.internal/dula
helm upgrade --install dula deploy/helm/dula -n dula-prod --create-namespace \
  -f deploy/helm/dula/values-airgapped.yaml
```

The air-gapped profile permits **no external egress** and keeps connector egress off; verify with
`deploy/airgap/verify-airgap.sh`.

## Upgrades

Upgrades are rolling and zero-downtime by design (`maxUnavailable: 0`); schema changes run as a
**forward-only** pre-upgrade migration Job. Always deploy a **signed** image (Kyverno blocks
unsigned/unattested images).

```bash
helm upgrade dula deploy/helm/dula -n dula-prod -f deploy/helm/dula/values-cloud.yaml
```

## Backup & restore

```bash
export DATABASE_URL=postgres://user:pass@host:5432/dula
deploy/backup/pg-backup.sh ./backups
deploy/backup/pg-restore.sh ./backups/dula-<ts>.dump
```

See [../11-Deployment/DisasterRecovery.md](../11-Deployment/DisasterRecovery.md).

## Observability

Import `deploy/observability/grafana-dashboard.json` into Grafana and apply
`deploy/observability/prometheus-rules.yaml`. SLO targets and alert meanings:
[../16-Operations/Observability.md](../16-Operations/Observability.md).

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| Pods rejected at admission | Image not signed, or missing security context — deploy a signed image; the chart already sets the required context. |
| `dula-secrets` not found | Create the Secret (Vault/SOPS) before installing; the chart references it, never inlines it. |
| Migration Job fails | Check `DATABASE_URL`; the Job runs `alembic upgrade head` before the new pods roll. |
| Air-gapped pods can't pull | Ensure images were pushed to the private mirror and `global.imageRegistry` points at it. |
