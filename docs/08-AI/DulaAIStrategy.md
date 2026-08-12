---
title: Dula AI Strategy
document_id: AI-001
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: AI
audience: AI/ML engineers, leadership
phase: Documentation Bootstrap (M000)
related:
  - ./ModelSelection.md
  - ./FineTuningStrategy.md
  - ./EvaluationStrategy.md
  - ../02-Vision/ProductStrategy.md
---

# Dula AI Strategy

> **Purpose.** Define the staged path to a cybersecurity-specialized model. The strategy
> **does not** assume training a foundation model from scratch. Each stage is justified by
> a concrete trigger and gated by evaluation. Advancing a stage is only worthwhile if it
> beats the previous stage on the internal benchmark at acceptable cost.

## 1. Guiding Logic

Complexity and cost rise sharply up the stages; value does not always rise with them.
**Climb only as far as the evaluation and business case justify.** Most production value
is expected from stages 1–9. Stages 12–15 are **RESEARCH/EXPERIMENTAL**.

```mermaid
flowchart LR
    S1[1 Open base model] --> S2[2 Prompt eng] --> S3[3 RAG] --> S4[4 Tool calling]
    S4 --> S5[5 Datasets] --> S6[6 Benchmark] --> S7[7 Instruction tuning]
    S7 --> S8[8 LoRA] --> S9[9 QLoRA] --> S10[10 Quantization]
    S10 --> S11[11 Optimization] --> S12[12 Distillation] --> S13[13 Specialized models]
    S13 --> S14[14 Advanced training] --> S15[15 Pretraining from scratch]
```

## 2. Stage-by-Stage

| # | Stage | What | Justified when | Maturity |
|---|-------|------|----------------|----------|
| 1 | Open-source foundation model | Adopt a permissively-licensed base model | Always the start | MVP |
| 2 | Prompt engineering | System prompts, templates, few-shot | Immediately; cheapest lever | MVP |
| 3 | RAG | Ground answers in security knowledge | Need factual, cited, up-to-date answers | MVP |
| 4 | Tool calling | Let model invoke tools | Tasks need live data/actions | MVP→FUTURE |
| 5 | Cybersecurity datasets | Curate licensed security data | Before any tuning/eval | MVP |
| 6 | Evaluation benchmark | Build the internal benchmark | **Before** tuning — gates all later stages | MVP |
| 7 | Instruction tuning | SFT on security instructions | Prompt+RAG plateau on measured tasks | FUTURE |
| 8 | LoRA | Parameter-efficient fine-tune | Need domain adaptation cheaply | FUTURE |
| 9 | QLoRA | Quantized LoRA for larger models on less VRAM | Hardware-constrained tuning | FUTURE |
| 10 | Quantization | INT8/INT4 for serving | Deploy on limited/air-gapped hardware | FUTURE |
| 11 | Model optimization | Batching, caching, distillation-lite, speculative decode | Latency/throughput/cost pressure | FUTURE |
| 12 | Distillation | Train smaller model from larger | Need small fast model at quality | RESEARCH |
| 13 | Specialized models | Task-specific small models (e.g. classify, extract) | A task is high-volume & narrow | RESEARCH |
| 14 | Advanced training | Preference optimization (DPO/RLAIF), continued pretraining on domain corpus | Clear, measured ceiling from SFT/LoRA | RESEARCH |
| 15 | Pretraining from scratch | Train a base model | Only if licensing/quality/sovereignty *cannot* be met otherwise — very high cost | RESEARCH (likely never) |

## 3. When Fine-Tuning Beats RAG (and Vice Versa)

- **Prefer RAG** for knowledge that changes (CVEs, advisories), needs citations, or is
  tenant-specific. Do **not** fine-tune facts that RAG can supply.
- **Prefer fine-tuning** for *behavior/format/reasoning style* (e.g. producing Sigma
  rules, consistent triage structure) that prompting can't reliably achieve.
- Often the answer is **both**: a tuned model that reasons well over RAG evidence.

## 4. Gating: Evaluation First

Stage 6 (benchmark) is built **before** any tuning. No later stage ships unless it beats
the current production configuration on the benchmark with no safety regressions
([./EvaluationStrategy.md](./EvaluationStrategy.md), [./Benchmarking.md](./Benchmarking.md)).

## 5. Hardware & Cost Awareness

- Inference target includes CPU/air-gapped (quantized) — see
  [./InferenceArchitecture.md](./InferenceArchitecture.md).
- Training hardware needs are estimated (not measured) in
  [./TrainingStrategy.md](./TrainingStrategy.md) — **REQUIRES RESEARCH** before commitment.

## 6. Risks

- Over-investing in tuning before evaluation exists (mitigated by §4).
- Dataset licensing/quality (see [./DatasetStrategy.md](./DatasetStrategy.md)).
- Safety regressions from tuning (dual-use content) — covered by
  [../10-Security/AIThreatModel.md](../10-Security/AIThreatModel.md).

## Related Documents

- [./ModelSelection.md](./ModelSelection.md) · [./FineTuningStrategy.md](./FineTuningStrategy.md) ·
  [./AIResearchRoadmap.md](./AIResearchRoadmap.md)
