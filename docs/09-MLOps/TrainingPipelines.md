---
title: Training Pipelines
document_id: MLO-004
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: MLOps
audience: AI/ML engineers
phase: Documentation Bootstrap (M000)
related:
  - ../08-AI/TrainingStrategy.md
  - ./ExperimentTracking.md
  - ./EvaluationPipelines.md
---

# Training Pipelines

> **Purpose.** Define the automated, reproducible pipelines that produce model artifacts.

## 1. Orchestration

- **Argo Workflows** on Kubernetes; pipeline definitions live in `ml/training` as code.
- Each pipeline is parameterized (dataset version, base model, hyperparameters) and fully
  tracked ([./ExperimentTracking.md](./ExperimentTracking.md)).

## 2. Pipeline Stages

```mermaid
flowchart LR
    IN[Inputs: dataset vX + base model + config] --> PREP[Prepare/tokenize]
    PREP --> TRAIN[Train SFT/LoRA/QLoRA]
    TRAIN --> EVAL[Evaluate vs benchmark]
    EVAL --> REG[Register candidate + report]
```

## 3. Reproducibility

- Pinned containers (CUDA/PyTorch), deterministic seeds, recorded configs, dataset version
  hashes; re-running the pipeline reproduces the artifact within variance.

## 4. Resource Management

- GPU scheduling via K8s; jobs sized per task; cost/time recorded. Hardware needs are
  estimates until measured ([../08-AI/TrainingStrategy.md](../08-AI/TrainingStrategy.md)).

## 5. Safety Steps

- Data safety filtering pre-train; safety evaluation post-train is part of the eval stage
  ([../10-Security/AIThreatModel.md](../10-Security/AIThreatModel.md)).

## 6. Gate

- The pipeline registers a **candidate** only; promotion happens via
  [./EvaluationPipelines.md](./EvaluationPipelines.md) + [./ModelLifecycle.md](./ModelLifecycle.md).
