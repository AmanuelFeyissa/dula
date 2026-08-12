---
title: Milestone Closure — M004 (Phase 04 Dula AI) — Complete (first candidate retired)
document_id: MVP-M004-CLOSURE
status: Reviewed
version: 1.0.0
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

> Produced per **CLAUDE.md §11.8**. **This milestone is COMPLETE.** The train→eval→gate→
> register→serve pipeline is delivered and CI-green, **and a real QLoRA run was executed on free
> compute (ADR-0012) producing a recorded ship/retire decision** — the first candidate was
> **RETIRED** (it did not beat the general model and regressed safety), so the platform stays on
> the general model + RAG. Per Phase 04 acceptance, the milestone completes on a retire outcome;
> shipping a worse model is never acceptable.

## Run results & decision (first candidate)

Executed on a free-credit Modal L4 (train + eval, a few minutes, cents):

| Metric | Candidate (Primus-tuned) | Baseline (general model) |
|--------|--------------------------|--------------------------|
| Base model | Qwen2.5-0.5B-Instruct (QLoRA) | Qwen2.5-0.5B-Instruct |
| Benchmark accuracy (MMLU computer_security, 100 MCQ) | **0.360** | **0.370** |
| Safety refusal rate (4 adversarial) | **0.250** | **0.500** |
| Dataset | trendmicro-ailab/Primus-Instruct (ODC-BY/MIT) | — |

**Gate → RETIRE:** quality did not beat baseline (0.360 < 0.370) **and** safety regressed
(0.250 < 0.500). The candidate was **not shipped**; nothing was pushed to the model repo. Record:
`ml/registry/registry.jsonl` + model card `ml/registry/dula-ai-secqa-qlora-v0.1-card.md`.

**Reading of the result (honest):** a 0.5B model tuned on Primus's report-writing tasks did not
improve multiple-choice security-knowledge accuracy and reduced refusals — a correct, expected
first-iteration outcome that validates the *gate* end to end. Future iterations (larger base
e.g. Qwen2.5-3B/7B, safety-preserving data mix, task-aligned eval) are a config change on the
same pipeline; each must clear the same gate to ship.

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

## Executed acceptance step
- **A real QLoRA candidate was trained, evaluated, and decided** (see *Run results & decision*):
  decision **RETIRE**, recorded in `ml/registry/`. Connections verified: Hugging Face, Modal,
  Kaggle. Since the candidate was retired, no artifact was pushed and canary/rollback +
  quantized variants are not exercised this iteration (they engage only when a candidate ships).

## Documentation Impact Assessment (CLAUDE.md §11.6)
1. **Implemented:** the pipeline + gate + serving path (above).
2. **Technical docs created:** ADR-0012; [Dula AI Training & Release Runbook](../../16-Operations/DulaAITrainingRunbook.md); this closure.
3. **Technical docs updated:** TrainingPipelines, ModelRegistry (status notes), ADR index, SUMMARY, Glossary, PROJECT_STATE, PROJECT_CONTEXT.
4. **User docs:** none required — Dula AI stayed internal (candidate retired); the Ask UI is unchanged (model swaps behind the gateway).
5. **Model card + registry entry** produced for the real candidate: `ml/registry/dula-ai-secqa-qlora-v0.1-card.md`, `ml/registry/registry.jsonl`.
6. **Examples/commands verified:** torch-free logic + provider via CI tests; the real GPU run executed on Modal (ADR-0012).
7. **Links valid:** `tools/check-doc-links.sh` passes. 8. **Diagrams:** existing AI/MLOps diagrams still accurate.
9. **Incomplete items:** none for M004. 10-11. **Gaps:** larger-base iterations + a broader eval suite are future work, not M004 gaps.

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
- First candidate is a **0.5B** model tuned instruct-only for speed/cost; larger bases
  (Qwen2.5-3B/7B), a safety-preserving data mix (add Primus-Reasoning + refusal data), and a
  broader eval suite are future iterations — each must clear the same gate to ship.
- Benchmark is MMLU `computer_security` (100 MCQ, MIT) + 4 adversarial prompts; expand the
  held-out suite (e.g. CTIBench, more safety items) for a stronger signal.
- Near-dup detection is exact-only (MinHash/embedding dedup future); merge requires a non-4bit
  base (adapter-only fallback otherwise).

## Next steps / status
- **Next (future iterations):** rerun the same pipeline with a larger base + improved data/eval;
  a shipping candidate would be registered, pushed to `AmanuelFeyissa/dula-ai`, and served behind
  the gateway (`provider=openai`) with canary/rollback. Repeatable for free on Kaggle.
- **Final status:** **COMPLETE** — pipeline delivered + CI-green, and a real candidate was
  trained, evaluated, and **retired** with the decision recorded. Phase 04 acceptance is met on
  the retire outcome; shipping a worse model is never acceptable.
