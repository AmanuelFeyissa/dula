---
title: Phase 04 — Dula AI
document_id: MVP-004
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: AI / MLOps
audience: All contributors
phase: Documentation Bootstrap (M000)
related:
  - ../08-AI/DulaAIStrategy.md
  - ../08-AI/FineTuningStrategy.md
---

# Phase 04 — Dula AI

> **Purpose.** Introduce the first cybersecurity-specialized model behind the gateway,
> shipped **only if it beats the general model** on the benchmark.

## Objective
Deliver instruction-tuned / LoRA-adapted Dula AI (Stages 5–9), served via the gateway,
gated by evaluation, with the MLOps foundations to reproduce it.

## Scope
- Dataset pipeline for security instruction data ([../08-AI/DataPipeline.md](../08-AI/DataPipeline.md)).
- SFT/LoRA/QLoRA training pipeline ([../08-AI/FineTuningStrategy.md](../08-AI/FineTuningStrategy.md),
  [../09-MLOps/TrainingPipelines.md](../09-MLOps/TrainingPipelines.md)).
- Model registry + evaluation pipeline + canary serving
  ([../09-MLOps/ModelRegistry.md](../09-MLOps/ModelRegistry.md),
  [../09-MLOps/DeploymentPipelines.md](../09-MLOps/DeploymentPipelines.md)).
- Quantized variants for on-prem/air-gapped ([../08-AI/ModelOptimization.md](../08-AI/ModelOptimization.md)).

## Dependencies
- Phase 03 (benchmark + gateway + RAG) complete; base model selected (ADR-0007).

## Deliverables
- A registered Dula AI version passing the eval+safety gate; canary → production behind the
  gateway with rollback.

## Implementation Requirements
- Full experiment tracking + dataset versioning ([../09-MLOps/README.md](../09-MLOps/README.md));
  reproducible pipelines.

## Tests
- Benchmark comparison vs general model; **safety must not regress**; contamination = 0
  ([../08-AI/EvaluationStrategy.md](../08-AI/EvaluationStrategy.md)).

## Security Requirements
- Training-data safety filtering; post-train adversarial evaluation; artifact integrity
  ([../10-Security/AIThreatModel.md](../10-Security/AIThreatModel.md)).

## Documentation
- Model card + eval report in registry; Dula AI ops notes; update PROJECT_STATE.

## Acceptance Criteria
- **Either** a Dula AI candidate beats the general model on the benchmark with no safety
  regression and its quantized variant runs on target on-prem hardware — **or** the phase
  concludes with a documented finding that adaptation did not beat RAG-on-general-model yet,
  the candidate is **retired** (not shipped), and the platform continues on the general
  model. *The milestone completes in both cases* — it must not stall on model quality
  (M000 review R3/U3). Shipping a worse model is never acceptable.

## Definition of Done
- Global DoD + above; rollback path proven; decision (ship vs retire) recorded with the
  eval report.
