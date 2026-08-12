# ADR-0012: Dula AI Training Compute & Artifact Hosting

- Status: Accepted
- Date: 2026-08-12
- Deciders: Project owner (user), AI/MLOps
- Related: [ADR-0005](./ADR-0005-model-serving-runtime.md), [ADR-0007](./ADR-0007-base-model.md), [ADR-0010](./ADR-0010-mlops-tooling.md), [../08-AI/FineTuningStrategy.md](../08-AI/FineTuningStrategy.md), [../09-MLOps/TrainingPipelines.md](../09-MLOps/TrainingPipelines.md)

## Context
Phase 04 trains **Dula AI** (Product 2). The project owner's local machine has **no GPU** and a
space-constrained disk, so training and heavy artifacts must live off the local machine. We need
compute for fine-tuning/evaluation, a home for datasets and model weights, and a path to a demo —
without abandoning the existing GitHub source-of-truth + CI, and without locking the project into
a vendor. Choices must be **futurity-aware** (scale into paid tiers without re-architecting) and
consistent with deploy-anywhere/air-gapped (ADR-0005) and permissive base models (ADR-0007).

## Options Considered
1. **Single all-in-one platform** (e.g. move repo + compute to one vendor) — simplest mental
   model, but no free-GPU host doubles as a good monorepo/CI home, and it creates lock-in.
2. **Buy GPU / paid cloud from the start** — reliable but not free; premature for an unproven
   fine-tune that may be *retired* (Phase 04 allows retirement).
3. **Composition: keep GitHub; add Hugging Face Hub for artifacts; use free GPU tiers for
   training** — no single lock-in; each piece scales into paid tiers.

## Decision
Adopt the **composition (option 3)**:

- **Source of truth + CI:** stay on **GitHub** (monorepo `dula`, ADR-0011). Do not migrate off.
- **Datasets & model weights (registry/artifacts):** **Hugging Face Hub** (private repos), git-based,
  complementing GitHub and fitting MLflow/DVC (ADR-0010) and model provenance (ADR-0007).
- **Training/eval GPU (free):** **Kaggle** (~30 GPU hrs/week, primary), **Lightning AI**
  (~80 GPU hrs/month, iterative), and **Modal** ($30/month credits, reproducible scripted jobs),
  using **QLoRA** so 3B–7B permissive bases (Qwen/Mistral) fit free T4/L4.
- **Demo (optional):** a **Hugging Face Space (ZeroGPU)** for inference demos (free ≈ 5 min/day
  GPU, Gradio, inference-only — not training, not production).
- **Production serving:** unchanged from ADR-0005 — self-hosted **vLLM (GPU) / llama.cpp
  (CPU/air-gapped)** behind the LLM Gateway, on customer/target infrastructure. There is **no
  sustainable free 24/7 GPU** for production; a free always-on *demo* can serve a quantized small
  model on CPU via llama.cpp.

The heavy training code (torch/transformers/peft/trl) lives in the standalone `ml/` project (run
on the above accounts); the quality/safety-critical logic lives in the torch-free, CI-tested
`packages/dula-ml`, so the training rules match CI. A shipped checkpoint is served behind the
gateway via the OpenAI-compatible provider — no application changes.

## Consequences
- No vendor lock-in; each component scales into a paid tier independently (Kaggle→Modal/RunPod;
  HF free→Team/Enterprise; demo Space→dedicated endpoint) without re-architecting.
- Requires the owner to hold accounts/tokens (HF write token, Kaggle, Lightning, Modal); Dula
  provides ready notebooks/runners and pauses at the real-GPU step for those tokens.
- Free GPU quotas are modest and interruptible — fine for QLoRA of small/mid models and eval,
  not for large pretraining (from-scratch pretraining remains RESEARCH/likely-never per strategy).
- The local machine stays clear of heavy artifacts; large files go to HF or the F: drive, not C:.

## Compliance / Verification
- Base models remain permissive (ADR-0007); dataset licenses pass the gate (Primus: ODC-BY/MIT).
- Model-weight provenance/hashes verified on load (supply chain); artifacts carry a model card +
  eval report (ModelRegistry.md). Serving path is model-agnostic (ADR-0005); air-gapped profiles
  never depend on any external host.
