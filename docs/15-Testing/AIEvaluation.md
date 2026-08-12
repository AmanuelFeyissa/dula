---
title: AI Evaluation (Testing)
document_id: TST-006
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: AI / QA
audience: AI & QA engineers
phase: Documentation Bootstrap (M000)
related:
  - ../08-AI/EvaluationStrategy.md
  - ../08-AI/Benchmarking.md
  - ./AgentEvaluation.md
---

# AI Evaluation (Testing View)

> **Purpose.** The testing-side view of AI evaluation. Strategy and gates are defined in
> [../08-AI/EvaluationStrategy.md](../08-AI/EvaluationStrategy.md); this describes how it
> runs as part of the testing/CI program.

## 1. What Runs

- Benchmark suites ([../08-AI/Benchmarking.md](../08-AI/Benchmarking.md)) for model + RAG:
  knowledge QA/groundedness, detection authoring, CTI extraction, safety/adversarial.

## 2. Triggers

- On every model/prompt/RAG change, and scheduled for drift detection.

## 3. Scoring

- Automated/structured scoring + LLM-as-judge (human-calibrated) + sampled human expert
  review ([../08-AI/EvaluationStrategy.md](../08-AI/EvaluationStrategy.md)).

## 4. Gate

- Must match/beat production on primary metrics and show **no safety regression**;
  otherwise blocked ([../09-MLOps/EvaluationPipelines.md](../09-MLOps/EvaluationPipelines.md)).

## 5. Anti-Contamination

- Zero-overlap assertion between training inputs and eval set enforced.

## 6. Reporting

- Reports attached to registry entries; trends tracked across releases.

## 7. Hallucination & Citations

- Explicitly measure hallucination rate and citation correctness for grounded tasks
  ([../08-AI/RAGEngineering.md](../08-AI/RAGEngineering.md)).
