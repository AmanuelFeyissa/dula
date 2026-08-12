---
title: On-Premises Deployment
document_id: DEP-005
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Platform / Ops
audience: Platform & ops engineers
phase: Documentation Bootstrap (M000)
related:
  - ./KubernetesDeployment.md
  - ./AirGappedDeployment.md
---

# On-Premises Deployment

> **Purpose.** Define fully self-hosted deployment in the customer's data center — no
> reliance on external services (air-gapped is a stricter variant).

## 1. Approach

- Same Helm charts on a customer-operated Kubernetes cluster.
- All data services self-hosted (Postgres, Qdrant, OpenSearch, Redis, MinIO,
  Redpanda/Kafka); models served locally (vLLM/llama.cpp).

## 2. Requirements

- Customer-provided K8s, storage, and (optionally) GPU nodes; ingress/TLS; internal DNS.
- Internal Vault/KMS for secrets/keys.
- Exact minimums **REQUIRES RESEARCH** and are captured in a sizing guide per release.

## 3. Networking

- May allow limited outbound (updates/TI feeds) or none; default-deny egress with explicit
  allowlists. For zero egress, use the air-gapped profile
  ([./AirGappedDeployment.md](./AirGappedDeployment.md)).

## 4. Updates

- Pull signed images from a customer registry (mirrored) or import from an offline bundle;
  forward-only migrations; canary model rollout.

## 5. Backup/DR

- Customer-owned backups of data stores + object storage + model artifacts
  ([../16-Operations/BackupRecovery.md](../16-Operations/BackupRecovery.md),
  [./DisasterRecovery.md](./DisasterRecovery.md)).

## 6. Support Model

- Diagnostics exportable without exposing sensitive data; remote support only if the
  customer permits connectivity.
