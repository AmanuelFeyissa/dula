---
title: Dula AI Training & Release Runbook
document_id: OPS-008
status: Draft
version: 0.1.0
last_updated: 2026-08-12
owner: AI / MLOps, DevOps/SRE
audience: ML Engineer, DevOps/SRE, Operator
phase: Phase 04 — Dula AI (M004)
related:
  - ../08-AI/FineTuningStrategy.md
  - ../09-MLOps/TrainingPipelines.md
  - ../09-MLOps/ModelRegistry.md
  - ../adr/ADR-0012-training-and-hosting.md
  - ../12-API/AIGatewayAPI.md
---

# Dula AI Training & Release Runbook

> **Purpose.** Operate the Dula AI training → evaluation → **ship/retire** → serving loop.
> **Status: CURRENT** (pipeline + gate). Actual GPU training runs on external free compute
> (ADR-0012); the local machine has no GPU.

## Prerequisites (accounts/tokens)
- **Hugging Face** write token (datasets/model artifacts), **Kaggle** (`kaggle.json`),
  **Lightning AI** (phone-verified), optional **Modal** token. See
  [../adr/ADR-0012-training-and-hosting.md](../adr/ADR-0012-training-and-hosting.md).

## Pipeline (reproducible)
Steps (locally via `ml/dvc.yaml`, on a cluster via `deploy/argo/dula-ai-training-workflow.yaml`):

1. **prepare** — `dula_train.data_prep`: pull Primus (ODC-BY/MIT), map → SFT records, **safety
   filter → dedup → contamination check** (fails if any train row overlaps the benchmark).
2. **train** — `dula_train.train_qlora`: QLoRA SFT on a permissive base (Qwen2.5, ADR-0007), MLflow-logged.
3. **eval** — `dula_train.eval_runner` for the **candidate** and the **baseline** (general model).
4. **decide** — `dula_train.decide`: the `dula-ml` gate. **Ship** only if the candidate beats
   the baseline on the benchmark **and** does not regress safety; otherwise **retire**.

## The gate (non-negotiable)
- **Quality:** `candidate.accuracy ≥ baseline.accuracy (+delta)`.
- **Safety:** `candidate.safety_refusal_rate ≥ baseline − tolerance` (no regression).
- **Contamination = 0** (asserted at prepare time).
- **Shipping a worse model is never acceptable.** A retired candidate is a valid Phase 04
  outcome — the platform stays on the general model + RAG.

## Release (only on "ship")
1. Merge/quantize the adapter; produce GGUF/AWQ variants for CPU/air-gapped (ModelOptimization).
2. Register: model card + registry entry (`dula-ml`), push artifact to the HF Hub; verify weight hash.
3. Serve behind the gateway via an OpenAI-compatible endpoint (vLLM/llama.cpp): set
   `provider=openai`, `openai_base_url`, `openai_model` on `apps/ai-gateway` — **no app change**.
4. **Canary** in the gateway (route a fraction of traffic), watch metrics, then promote.

## Rollback
- The gateway is model-agnostic: revert `provider`/`openai_model` to the previous registered
  version (or back to `extractive`/general model). Registry manifest + model cards make the prior
  version and its eval report immediately identifiable.

## Safety & supply chain
- Training data is safety-filtered (drop operational-offensive teaching); post-train adversarial
  eval must not regress; model-weight provenance/hashes verified on load
  ([../10-Security/AIThreatModel.md](../10-Security/AIThreatModel.md)).
