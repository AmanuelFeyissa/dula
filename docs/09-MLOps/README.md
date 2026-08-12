---
title: MLOps — Overview
document_id: MLO-000
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: MLOps / AI
audience: MLOps & AI engineers
phase: Documentation Bootstrap (M000)
---

# 09 — MLOps

> **Purpose.** Define the operational backbone for the model lifecycle: tracking,
> dataset/model versioning, pipelines, evaluation gates, deployment, and monitoring —
> all self-hostable and air-gap capable.

## Tooling (candidates — ADR-0010)

| Concern | Tool | Alternatives |
|---------|------|--------------|
| Experiment tracking | MLflow | W&B, ClearML |
| Dataset versioning | DVC (+ object storage) | LakeFS, git-annex |
| Model registry | MLflow Registry | custom, ClearML |
| Pipelines | Argo Workflows (K8s) | Kubeflow, Prefect |
| Serving | vLLM/llama.cpp behind gateway | TGI, Ollama |

All chosen for self-hostability and offline operation
([../01-Project/TechnologyStack.md](../01-Project/TechnologyStack.md)).

## Documents

- [ExperimentTracking.md](./ExperimentTracking.md)
- [DatasetVersioning.md](./DatasetVersioning.md)
- [ModelRegistry.md](./ModelRegistry.md)
- [TrainingPipelines.md](./TrainingPipelines.md)
- [EvaluationPipelines.md](./EvaluationPipelines.md)
- [DeploymentPipelines.md](./DeploymentPipelines.md)
- [ModelLifecycle.md](./ModelLifecycle.md)

## Principle

**Reproducibility and evaluation gates are non-negotiable.** Every model in production is
traceable to its data, code, and eval report, and can be rolled back.
