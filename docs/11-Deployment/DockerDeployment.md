---
title: Docker Deployment
document_id: DEP-002
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Platform
audience: Platform & ops engineers
phase: Documentation Bootstrap (M000)
related:
  - ./LocalDevelopment.md
  - ./KubernetesDeployment.md
---

# Docker Deployment

> **Purpose.** Define single-host Docker Compose deployment — suitable for evaluation,
> small teams, and constrained on-prem/edge sites. Not the production baseline (that's K8s).

## 1. When to Use

- Evaluation/PoC, small single-node installs, edge sites without K8s.
- Not for HA or large scale — use Kubernetes ([./KubernetesDeployment.md](./KubernetesDeployment.md)).

## 2. Composition

- A production-oriented Compose profile brings up all core services + data stores + local
  model serving. Images are the same signed images used in K8s.

## 3. Configuration & Secrets

- Config via environment/mounted files; secrets via Docker secrets or a local Vault
  (not `.env`) — see [../10-Security/DataSecurity.md](../10-Security/DataSecurity.md).

## 4. Models

- Local serving (llama.cpp/Ollama) with quantized models sized to the host; GPU optional.

## 5. Upgrades & Backup

- Pull new signed images by digest; run DB migrations; back up volumes
  ([../16-Operations/BackupRecovery.md](../16-Operations/BackupRecovery.md)).

## 6. Air-Gapped

- Images/models imported from the offline bundle into a local registry
  ([./AirGappedDeployment.md](./AirGappedDeployment.md)).

## 7. Limitations

- No native autoscaling/HA; document capacity limits and when to migrate to K8s.
