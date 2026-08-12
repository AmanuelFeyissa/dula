---
title: Benchmarking
document_id: AI-009
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: AI
audience: AI/ML engineers
phase: Documentation Bootstrap (M000)
related:
  - ./EvaluationStrategy.md
  - ./DatasetStrategy.md
---

# Benchmarking

> **Purpose.** Define the internal cybersecurity benchmark that grounds every model claim.
> The benchmark is built **before** any fine-tuning (Stage 6 in
> [DulaAIStrategy.md](./DulaAIStrategy.md)).

## 1. Why an Internal Benchmark

Public benchmarks don't measure our security tasks and are prone to contamination. We need
a held-out, security-specific benchmark tied to our use cases
([../02-Vision/UseCases.md](../02-Vision/UseCases.md)).

## 2. Benchmark Composition (Planned)

| Suite | Measures | Maps to UC |
|-------|----------|-----------|
| Knowledge QA | ATT&CK/CVE/standards factual grounding (with citations) | UC-14, UC-01 |
| Log/alert reasoning | Interpret logs, triage correctly | UC-01, UC-06 |
| Detection authoring | Sigma/YARA correctness | UC-04 |
| CTI extraction | IOC/TTP extraction, STIX mapping | UC-05 |
| Vulnerability reasoning | CVE context/prioritization | UC-07 |
| Safety/adversarial | Prompt injection, exfiltration, dual-use handling | cross-cutting |
| Agent tasks | Multi-step task success + safety | UC-03, UC-15 |

Task counts, scoring rubrics, and pass thresholds are **REQUIRES RESEARCH** and defined
when the benchmark is authored.

## 3. Construction Rules

- Authored/validated by security experts; each item has a rubric or reference answer.
- Held out from all training and synthetic-generation inputs; zero-overlap enforced by
  hashing ([./DatasetStrategy.md](./DatasetStrategy.md)).
- Versioned; changes to the benchmark are themselves reviewed (a moving benchmark
  invalidates comparisons).

## 4. Scoring

- Mix of exact/structured scoring (extraction, rule syntax), automated metrics, and
  LLM-as-judge with human calibration ([./EvaluationStrategy.md](./EvaluationStrategy.md)).

## 5. Reporting

- Every model/config produces a benchmark report stored with its registry entry; results
  are comparable across versions via the fixed benchmark.

## 6. Anti-Gaming

- Guard against training-to-the-benchmark: keep a rotating private holdout; monitor for
  suspicious jumps; require expert review of large gains.

## Related Documents

- [./EvaluationStrategy.md](./EvaluationStrategy.md) · [../09-MLOps/EvaluationPipelines.md](../09-MLOps/EvaluationPipelines.md)
