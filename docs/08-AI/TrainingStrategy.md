---
title: Training Strategy
document_id: AI-003
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: AI
audience: AI/ML engineers
phase: Documentation Bootstrap (M000)
related:
  - ./FineTuningStrategy.md
  - ./DatasetStrategy.md
  - ../09-MLOps/TrainingPipelines.md
---

# Training Strategy

> **Purpose.** Define the overall approach to training/adapting Dula AI: environment,
> hardware, reproducibility, and where full training fits vs cheaper adaptation.
> All hardware/cost figures are **estimates (REQUIRES RESEARCH)** until measured.

## 1. Scope of "Training" Here

Per [DulaAIStrategy.md](./DulaAIStrategy.md), "training" mostly means **adaptation**
(instruction tuning, LoRA/QLoRA), not from-scratch pretraining (Stage 15,
RESEARCH/likely-never). Continued pretraining on a domain corpus is **RESEARCH** (Stage 14).

## 2. Training Environment

- Reproducible containers with pinned CUDA/PyTorch and dependency locks.
- Orchestrated as pipelines on Kubernetes (Argo Workflows) —
  [../09-MLOps/TrainingPipelines.md](../09-MLOps/TrainingPipelines.md).
- Experiment tracking (MLflow), dataset versioning (DVC) —
  [../09-MLOps/README.md](../09-MLOps/README.md).
- Deterministic seeds, logged configs, and full lineage for reproducibility.

## 3. Hardware (Estimates — REQUIRES RESEARCH)

| Task | Rough need (estimate) | Notes |
|------|-----------------------|-------|
| LoRA on small/mid model | 1× modern data-center GPU | feasible for iteration |
| QLoRA on larger model | 1–2× GPUs | quantization reduces VRAM |
| Full SFT on mid model | multi-GPU node | costlier |
| Continued pretraining | large multi-node cluster | RESEARCH only |

Exact VRAM/time depend on model size, sequence length, and dataset — **must be measured**,
not assumed. Air-gapped customers do **not** train; training happens in the vendor's or
customer's controlled training environment and models are shipped as artifacts.

## 4. Reproducibility & Lineage

- Every run records: dataset version, base model version, hyperparameters, code commit,
  container digest, hardware, seeds, and metrics.
- Outputs registered in the model registry with the eval report attached
  ([../09-MLOps/ModelRegistry.md](../09-MLOps/ModelRegistry.md)).

## 5. Safety in Training

- Training data is filtered to avoid degrading safety (no operational offensive content);
  post-training safety evaluation is mandatory
  ([../10-Security/AIThreatModel.md](../10-Security/AIThreatModel.md)).

## 6. Gate

- A trained artifact is a candidate only; it ships only after passing the evaluation gate
  ([./EvaluationStrategy.md](./EvaluationStrategy.md)).

## Related Documents

- [./FineTuningStrategy.md](./FineTuningStrategy.md) · [./DatasetStrategy.md](./DatasetStrategy.md)
