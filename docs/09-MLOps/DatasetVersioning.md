---
title: Dataset Versioning & Lineage
document_id: MLO-002
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: MLOps / Data
audience: AI/ML & data engineers
phase: Documentation Bootstrap (M000)
related:
  - ../08-AI/DatasetStrategy.md
  - ../08-AI/DataPipeline.md
  - ./ExperimentTracking.md
---

# Dataset Versioning & Lineage

> **Purpose.** Guarantee datasets are immutable, versioned, and traceable end-to-end.

## 1. Approach

- **DVC** tracks dataset versions with content hashing; large files in object storage
  (MinIO/S3). Metadata (source, license, provenance, pipeline run) stored alongside.
- Naming: `<domain>-<purpose>-v<major.minor>`
  ([../00-Governance/NamingConventions.md](../00-Governance/NamingConventions.md)).
- **LakeFS** is a candidate if DVC scaling is insufficient (ADR-0010).

## 2. Immutability & Splits

- Each version is immutable; changes create a new version.
- Splits (`train/validation/test/eval`) recorded; the **eval** split is isolated and
  never used in training ([../08-AI/DatasetStrategy.md](../08-AI/DatasetStrategy.md)).

## 3. Lineage

```mermaid
flowchart LR
    SRC[Sources + licenses] --> PIPE[Pipeline run + commit]
    PIPE --> DSV[Dataset vX.Y hash]
    DSV --> RUN[Training/eval run]
    RUN --> MODEL[Model version]
```

Every model version links back to exact dataset versions and the pipeline run that built
them — full lineage for audit and reproducibility.

## 4. Provenance & Licensing

- Provenance (source, acquisition method/date, license) is mandatory metadata; datasets
  failing the license gate cannot be registered
  ([../01-Project/Dependencies.md](../01-Project/Dependencies.md)).

## 5. Synthetic Data Records

- Model-generated data records generator model+version, prompt, and date; flagged as
  synthetic; validated before training use.

## 6. Contamination Control

- Automated zero-overlap assertion between training inputs and the benchmark/eval set
  ([../08-AI/Benchmarking.md](../08-AI/Benchmarking.md)).
