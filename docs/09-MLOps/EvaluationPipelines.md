---
title: Evaluation Pipelines
document_id: MLO-005
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: MLOps / AI
audience: AI/ML engineers, QA
phase: Documentation Bootstrap (M000)
related:
  - ../08-AI/EvaluationStrategy.md
  - ../08-AI/Benchmarking.md
  - ./ModelLifecycle.md
---

# Evaluation Pipelines

> **Purpose.** Automate the evaluation gate so quality/safety are measured consistently and
> block promotion on regression.

## 1. Triggering

- On every candidate model, prompt change, RAG change, and agent change; also on a
  schedule to detect drift.

## 2. Pipeline

```mermaid
flowchart LR
    CAND[Candidate config] --> RUN[Run benchmark suites]
    RUN --> SCORE[Automated + LLM-judge + sampled human]
    SCORE --> SAFE[Safety/adversarial suite]
    SAFE --> GATE{Beats prod & no safety regression?}
    GATE -->|yes| PASS[Mark promotable + attach report]
    GATE -->|no| FAIL[Block + record]
```

## 3. Gate Rules

- Encodes the rules in [../08-AI/EvaluationStrategy.md](../08-AI/EvaluationStrategy.md):
  must match/beat production on primary metrics and show **no** safety regression.

## 4. Reports

- Machine-readable + human-readable reports stored and attached to the registry entry
  ([./ModelRegistry.md](./ModelRegistry.md)); comparable across versions via the fixed
  benchmark ([../08-AI/Benchmarking.md](../08-AI/Benchmarking.md)).

## 5. Contamination Assertion

- Pipeline asserts zero overlap between training inputs and eval set before trusting
  results.

## 6. Air-Gapped

- Runs fully offline using local models and the bundled benchmark.
