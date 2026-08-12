---
title: Evaluation Strategy
document_id: AI-008
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: AI
audience: AI/ML engineers, QA
phase: Documentation Bootstrap (M000)
related:
  - ./Benchmarking.md
  - ../15-Testing/AIEvaluation.md
  - ../09-MLOps/EvaluationPipelines.md
---

# Evaluation Strategy

> **Purpose.** Define how we measure AI quality and safety so that **no model, prompt, RAG,
> or agent change ships without measured, non-regressing quality**. Evaluation gates the
> entire Dula AI strategy ([DulaAIStrategy.md](./DulaAIStrategy.md)).

## 1. What We Evaluate

| Layer | Dimensions |
|-------|------------|
| Model | Correctness, security-domain reasoning, format adherence, refusal-appropriateness, hallucination |
| RAG | Retrieval recall/precision, groundedness, citation correctness |
| Agents | Task success, safety (no unauthorized actions), efficiency (steps/cost), tool-use correctness |
| Safety | Dual-use handling, prompt-injection resistance, data-leak resistance |

## 2. Methods

- **Automated metrics** on the held-out benchmark (see [./Benchmarking.md](./Benchmarking.md)).
- **LLM-as-judge** for open-ended quality — with human spot-checks to calibrate the judge
  (the judge is itself validated to avoid blind trust).
- **Human expert review** for security correctness on a sampled set.
- **Adversarial/red-team suites** for safety (prompt injection, jailbreaks, exfiltration).

## 3. Gating Rules

- A change is promotable only if it **beats or matches** the current production config on
  primary metrics **and** shows **no regression** on safety metrics.
- Regressions block promotion regardless of average gains.
- Gates run in CI/eval pipelines ([../09-MLOps/EvaluationPipelines.md](../09-MLOps/EvaluationPipelines.md)).

## 4. Preventing Contamination

- Benchmark/eval data is isolated from all training/synthetic-generation inputs; overlap
  is asserted to be zero via hashing ([./DatasetStrategy.md](./DatasetStrategy.md)).

## 5. Continuous Evaluation

- Evaluations run on every model/prompt/RAG/agent change and on a schedule to catch drift
  (e.g. from updated knowledge indices).
- Results are versioned and attached to model-registry entries
  ([../09-MLOps/ModelRegistry.md](../09-MLOps/ModelRegistry.md)).

## 6. Metrics Are Estimates Until Measured

No target numbers are asserted in bootstrap; baselines are established when the benchmark
first runs (**REQUIRES RESEARCH/measurement**).

## Related Documents

- [./Benchmarking.md](./Benchmarking.md) · [../15-Testing/AIEvaluation.md](../15-Testing/AIEvaluation.md) ·
  [../15-Testing/AgentEvaluation.md](../15-Testing/AgentEvaluation.md)
