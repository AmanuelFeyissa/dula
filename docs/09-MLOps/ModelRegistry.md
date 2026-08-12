---
title: Model Registry
document_id: MLO-003
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: MLOps
audience: AI/ML & platform engineers
phase: Documentation Bootstrap (M000)
related:
  - ./ModelLifecycle.md
  - ./DeploymentPipelines.md
  - ../08-AI/InferenceArchitecture.md
---

# Model Registry

> **Purpose.** Single source of truth for model artifacts, versions, variants, stages, and
> their evaluation reports.

## 1. What the Registry Holds

- Model versions (base + adapters), with lineage to dataset/experiment.
- Variants per version (full, INT8, INT4, GGUF/AWQ) for different hardware.
- Evaluation/benchmark reports attached to each version.
- Stage tags: `staging`, `production`, `archived`.
- Naming per [../00-Governance/NamingConventions.md](../00-Governance/NamingConventions.md)
  (`dula-<base>-<task>-<method>-vX.Y`).

## 2. Tooling

- **MLflow Model Registry** (self-hosted, air-gap capable); artifacts in object storage.

## 3. Promotion Flow

```mermaid
flowchart LR
    NEW[Candidate version] --> EVAL[Eval gate]
    EVAL -->|pass| STG[staging]
    STG --> CANARY[Canary via gateway]
    CANARY -->|healthy| PROD[production]
    PROD --> ARCH[archived on supersede]
```

Promotion requires passing the evaluation gate
([../08-AI/EvaluationStrategy.md](../08-AI/EvaluationStrategy.md)); details in
[./ModelLifecycle.md](./ModelLifecycle.md).

## 4. Consumption

- The LLM gateway/serving loads models by registry reference and stage
  ([../08-AI/InferenceArchitecture.md](../08-AI/InferenceArchitecture.md)); air-gapped
  installs import registry contents via the offline bundle.

## 5. Rollback

- Previous `production` version is retained; rollback = re-point stage tag. Fast and
  auditable.

## 6. Access Control & Audit

- Registry access is authenticated/authorized; all stage changes are audited.
