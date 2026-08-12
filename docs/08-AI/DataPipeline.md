---
title: Data Pipeline (AI)
document_id: AI-006
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: AI / Data
audience: AI/ML & data engineers
phase: Documentation Bootstrap (M000)
related:
  - ./DatasetStrategy.md
  - ./RAGEngineering.md
  - ../09-MLOps/DatasetVersioning.md
---

# Data Pipeline (AI)

> **Purpose.** Define the pipeline that turns raw sources into versioned datasets for
> training/eval and into indexed content for RAG.

## 1. Pipeline Stages

```mermaid
flowchart LR
    RAW[Raw sources] --> ING[Ingest + license check]
    ING --> CLEAN[Clean / normalize]
    CLEAN --> DEDUP[Deduplicate]
    DEDUP --> PII[PII / sensitive scrub]
    PII --> SPLIT[Split train/val/test/eval]
    SPLIT --> VER[Version + hash + register]
    VER --> TRAIN[Training/eval datasets]
    VER --> INDEX[RAG index build]
```

## 2. Stage Details

- **Ingest + license check:** reject sources failing the license gate
  ([../01-Project/Dependencies.md](../01-Project/Dependencies.md)); record provenance.
- **Clean/normalize:** strip boilerplate, normalize encodings/formats, standardize
  security identifiers (ATT&CK IDs, CVE IDs).
- **Deduplicate:** exact + near-duplicate removal to prevent overfitting and eval leakage.
- **PII/sensitive scrub:** de-identify telemetry; block secrets/credentials.
- **Split:** maintain an isolated eval set (never trained on).
- **Version/register:** immutable dataset versions via DVC + registry
  ([../09-MLOps/DatasetVersioning.md](../09-MLOps/DatasetVersioning.md)).

## 3. RAG Indexing Branch

- Chunking + metadata + embedding + dual index (vector + BM25) —
  see [./RAGEngineering.md](./RAGEngineering.md) and
  [../03-Architecture/RAGArchitecture.md](../03-Architecture/RAGArchitecture.md).

## 4. Reproducibility

- Pipelines are code (in `ml/datasets`), parameterized by config, run in tracked pipeline
  jobs; each dataset version links to the exact pipeline run/commit.

## 5. Quality Checks

- Automated checks: schema validation, dedup ratio, PII scan pass, eval-overlap = 0,
  distribution sanity. Failures block dataset publication.

## 6. Air-Gapped

- The pipeline runs fully offline; sources are mirrored into internal storage before
  processing.

## Related Documents

- [./DatasetStrategy.md](./DatasetStrategy.md) · [./RAGEngineering.md](./RAGEngineering.md)
