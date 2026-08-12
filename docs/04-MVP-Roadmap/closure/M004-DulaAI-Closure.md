---
title: Milestone Closure — M004 (Phase 04 Dula AI) — Pipeline Delivered
document_id: MVP-M004-CLOSURE
status: In Progress
version: 0.1.0
last_updated: 2026-08-12
owner: Engineering
audience: Project Maintainer, Developer, Architect, Security Engineer, ML Engineer, DevOps/SRE
phase: Phase 04 — Dula AI (M004)
related:
  - ../Phase04-DulaAI.md
  - ../../adr/ADR-0012-training-and-hosting.md
  - ../../PROJECT_STATE.md
  - ./README.md
---

# Milestone Closure — M004 (Phase 04 Dula AI)

> Produced per **CLAUDE.md §11.8**. **This milestone is NOT yet COMPLETE.** The training/eval/
> gate/serve **pipeline** is delivered and CI-green; the acceptance criterion needs a real QLoRA
> run + a recorded **ship/retire decision**, which executes on the user's free GPU accounts
> (ADR-0012). This report documents the delivered pipeline and the remaining step.

- **Milestone identifier:** M004
- **Milestone name:** Phase 04 — Dula AI
- **Objective:** Deliver an instruction-tuned/LoRA Dula AI behind the gateway, **gated by
  evaluation**, with reproducible MLOps — shipped **only if it beats the general model** with no
  safety regression; otherwise retired. See [../Phase04-DulaAI.md](../Phase04-DulaAI.md).

## Delivered this milestone (pipeline)
- **`packages/dula-ml`** (torch-free, CI-tested): SFT record formatting/mapping, dedup,
  **benchmark contamination check** (contamination = 0), training-data **safety filter**,
  evaluation scoring (MCQ + safety refusal), the **ship/retire gate**, registry manifest, and
  model-card rendering.
- **`ml/`** standalone GPU project: `dula_train` (`config`, `data_prep`, `train_qlora` QLoRA/SFT,
  `eval_runner`, `decide`), a seed security benchmark, Kaggle/Lightning/Modal runners,
  `requirements.txt`, `dvc.yaml`, and `deploy/argo/dula-ai-training-workflow.yaml` (Argo). Uses
  MLflow (ADR-0010). **Not** in the uv workspace, so CI/local stay torch-free and disk-light.
- **Serving:** `OpenAICompatProvider` in `dula-ai` + `provider=openai` in `apps/ai-gateway` — a
  shipped checkpoint (vLLM/llama.cpp) plugs behind the gateway with **no app change**.
- **ADR-0012** (Accepted): free GPU training (Kaggle/Lightning/Modal) + Hugging Face Hub for
  datasets/models; keep GitHub for code/CI; Primus (ODC-BY/MIT) datasets; Qwen/Mistral base.

## Technical / Security / AI-ML changes
- **AI/ML:** the full adapt→measure→decide loop exists as code; the decision rule is torch-free
  and identical in CI and on the runner.
- **Security (AIThreatModel/DatasetStrategy):** training-data safety filtering (drop operational-
  offensive teaching), contamination=0 assertion, model-weight hash recorded for provenance, and
  the safety-no-regression gate. Serving inherits the gateway's guardrails/tenant-isolation/audit.
- **Architecture:** model-agnostic serving preserved (ADR-0005); no coupling to a specific model.

## Testing performed (this milestone)
- `ruff` + `ruff format --check` clean; `mypy --strict` clean (64 source files; `ml/` excluded —
  torch env, validated on the runner); **80 pytest pass** (incl. dula-ml records/dedup/
  contamination/safety/evaluation/registry + the OpenAI-compat provider, mocked).
- The gate logic is unit-tested for both **ship** and **retire** outcomes and for a safety-
  regression veto.

## What is NOT done (the remaining acceptance step)
- **No trained Dula AI checkpoint yet.** The actual QLoRA training, candidate-vs-baseline
  evaluation, and the recorded **ship/retire decision** require a GPU and run on the user's free
  accounts (Kaggle/Lightning/Modal + Hugging Face). Per Phase 04 acceptance, the milestone
  completes in **both** outcomes (ship or retire) — but a decision must be produced and recorded.
- Quantized variants (GGUF/AWQ) and canary/rollback are exercised only once a candidate ships.

## Documentation Impact Assessment (CLAUDE.md §11.6)
1. **Implemented:** the pipeline + gate + serving path (above).
2. **Technical docs created:** ADR-0012; [Dula AI Training & Release Runbook](../../16-Operations/DulaAITrainingRunbook.md); this closure.
3. **Technical docs updated:** TrainingPipelines, ModelRegistry (status notes), ADR index, SUMMARY, Glossary, PROJECT_STATE, PROJECT_CONTEXT.
4. **User docs:** none required yet — Dula AI is internal until a candidate ships; the Ask UI is unchanged (the model swaps behind the gateway).
5. **Intentionally not created (N/A):** model card *content* for a real model, quantization/canary guides — pending an actual trained candidate.
6. **Examples/commands verified:** the torch-free logic + provider via CI tests; GPU commands documented in the runbook/`ml/README.md` (run externally).
7. **Links valid:** `tools/check-doc-links.sh` passes. 8. **Diagrams:** existing AI/MLOps diagrams still accurate.
9. **Incomplete items:** the trained model + decision (external GPU step). 10-11. **Gaps:** model card/eval report for a real candidate pending the run.

## Milestone Documentation Checklist (CLAUDE.md §11.7) — pipeline scope
### Technical
- [x] Architecture updated · [N/A] API (no new endpoints; provider config documented) · [N/A] Database
- [x] Configuration documented (train/eval/serving config) · [x] Security documentation updated
- [x] Deployment updated (Argo/DVC/runners) · [x] Testing documentation updated · [~] Troubleshooting (runbook)
- [x] Operational documentation updated (training runbook) · [x] AI/ML updated · [x] MLOps updated · [N/A] RAG/Agent/Plugin
### User
- [N/A] User/Admin/Operator guides — internal milestone; no user-facing change yet
### Quality
- [x] Front matter · [x] Naming (`dula-<base>-<task>-<method>-vX.Y`) · [x] Links validated
- [x] Commands verified (CI logic; GPU docs) · [x] No FUTURE-as-CURRENT · [x] SUMMARY updated
- [x] Glossary terms added · [x] PROJECT_CONTEXT/STATE updated

## Known limitations / deferred
- Offline `--smoke` train needs the torch env; real training is GPU-only (external).
- Seed benchmark is illustrative — swap in a real held-out suite (CyberMetric/SecEval/CTIBench)
  for a meaningful ship/retire measurement.
- Near-dup detection is exact-only (MinHash/embedding dedup future); reranker/embeddings from Phase 03 still apply.

## Next steps / status
- **Next:** user provides tokens → run `ml/` training on free GPU → evaluate candidate vs the
  general model → `decide` records **ship** or **retire** → register + (if ship) serve behind the
  gateway with canary/rollback → then finalize M004 and write the **Phase 04 Completion Review**.
- **Final status:** **PIPELINE DELIVERED — NOT YET COMPLETE** (awaiting the GPU training run and
  the recorded ship/retire decision). Shipping a worse model is never acceptable.
