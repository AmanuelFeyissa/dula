---
title: Model Deployment Pipelines
document_id: MLO-006
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: MLOps / Platform
audience: MLOps & platform engineers
phase: Documentation Bootstrap (M000)
related:
  - ./ModelRegistry.md
  - ./ModelLifecycle.md
  - ../08-AI/InferenceArchitecture.md
---

# Model Deployment Pipelines

> **Purpose.** Define how a promoted model reaches production serving safely, with canary
> and rollback, across deployment profiles.

## 1. Flow

```mermaid
flowchart LR
    REG[Registry: staging] --> PKG[Package variant for target hardware]
    PKG --> DEP[Deploy to serving pool]
    DEP --> CAN[Canary traffic via gateway]
    CAN -->|healthy metrics| PROMO[Promote to production]
    CAN -->|regression| RB[Rollback]
```

## 2. Canary & Rollout

- The LLM gateway routes a fraction of traffic to the candidate; live quality/safety and
  latency are monitored before full promotion.
- Rollback = re-point the `production` stage tag ([./ModelRegistry.md](./ModelRegistry.md)).

## 3. Profile Awareness

- Cloud/on-prem: pull variant from registry; GPU or CPU pool per hardware.
- **Air-gapped:** model variants ship in the offline bundle; "deploy" = load bundled
  artifact; no external pull ([../11-Deployment/AirGappedDeployment.md](../11-Deployment/AirGappedDeployment.md)).

## 4. GitOps

- Serving config (which model/stage per environment) is declarative and delivered via Argo
  CD, keeping deployments auditable and reversible.

## 5. Safety

- A model cannot be deployed unless its registry entry shows a passing eval+safety gate
  ([./EvaluationPipelines.md](./EvaluationPipelines.md)).
