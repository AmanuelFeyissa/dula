---
title: Phase Completion Review — Phase 04 (Dula AI)
document_id: MVP-P04-COMPLETION
status: Reviewed
version: 1.0.0
last_updated: 2026-08-12
owner: Engineering
audience: Project Maintainer, Architect, Developer, Security Engineer, ML Engineer, DevOps/SRE
phase: Phase 04 — Dula AI
related:
  - ../Phase04-DulaAI.md
  - ./M004-DulaAI-Closure.md
  - ../../adr/ADR-0012-training-and-hosting.md
  - ../../PROJECT_STATE.md
---

# Phase Completion Review — Phase 04 (Dula AI)

> Produced per **CLAUDE.md §11.9**. Phase 04 contains one milestone (M004); its
> [closure report](./M004-DulaAI-Closure.md) holds the detailed §11.6/§11.7 assessment and the
> run results.

## Phase objective
Introduce the first cybersecurity-specialized model behind the gateway — shipped **only if it
beats the general model** on the benchmark with no safety regression; otherwise retired and the
platform continues on the general model.

## Milestones completed
- **M004 — Dula AI:** COMPLETE ([M004 closure](./M004-DulaAI-Closure.md)). First candidate **retired**.

## Features / capability delivered
- Reproducible **train → eval → gate → register → serve** pipeline: torch-free, CI-tested
  `packages/dula-ml` (formatting, dedup, contamination check, safety filter, MCQ + safety
  scoring, ship/retire gate, registry, model card) + standalone `ml/` GPU project
  (`dula_train`: data_prep/train_qlora/eval_runner/decide) with DVC + Argo + MLflow.
- **Serving path:** OpenAI-compatible provider so a shipped checkpoint (vLLM/llama.cpp) serves
  behind the existing LLM Gateway with no app change.
- **A real, executed run:** Qwen2.5-0.5B QLoRA on Primus-Instruct (ODC-BY/MIT), evaluated vs the
  general-model baseline on MMLU `computer_security` (MIT) + an adversarial safety suite, with the
  decision recorded in `ml/registry/`.

## Result & decision
Candidate accuracy 0.360 vs baseline 0.370; safety-refusal 0.250 vs 0.500 → **RETIRE** (did not
beat quality **and** regressed safety). Nothing shipped; platform stays on the general model + RAG.
This is a correct first-iteration outcome that **validates the evaluation gate end-to-end** — the
whole point of Phase 04 is that quality/safety, not effort, decides what ships.

## Architecture delivered
Model-agnostic serving preserved (ADR-0005); the training/hosting split (free GPU + Hugging Face
Hub + GitHub) is fixed in **ADR-0012**. The pipeline is identical in CI (torch-free logic) and on
the GPU runner, so the gate can't drift.

## Security posture
Training-data safety filtering (drop operational-offensive teaching), **contamination = 0**
(asserted at prepare time), a **safety-no-regression veto** in the gate (which correctly fired
here), and model-weight provenance/hashing for anything that would ship. Aligns with
[../../10-Security/AIThreatModel.md](../../10-Security/AIThreatModel.md).

## Testing status
`ruff`/`ruff format`/`mypy --strict` clean; **81 pytest** (incl. dula-ml formatting/dedup/
contamination/safety/evaluation/registry + provider); the pipeline was additionally proven
end-to-end on Modal (cheap CPU validation, then the real GPU run).

## Documentation status
ADR-0012, Dula AI Training & Release Runbook, TrainingPipelines/ModelRegistry status notes, model
card + registry entry (`ml/registry/`), SUMMARY/Glossary/PROJECT_STATE/PROJECT_CONTEXT updated;
links validated.

## User-documentation status
None required — Dula AI stayed internal (candidate retired); the Ask UI is unchanged (a shipped
model swaps in behind the gateway without user-facing change).

## Known limitations / technical debt / deferred
- First candidate is a small (0.5B), instruct-only tune for speed/cost. Larger bases
  (Qwen2.5-3B/7B), a safety-preserving data mix, and a broader eval suite (e.g. CTIBench, more
  safety items) are future iterations on the same pipeline.
- Merge requires a non-4bit base (adapter-only fallback otherwise); near-dup dedup is exact-only.
- Live Kaggle-driven runs (free, repeatable) are wired but this decision was produced on Modal
  free credit for reliability.

## Outstanding risks
Model quality vs the general model remains an open empirical question (expected — resolved by
iterating and re-running the gate). Base-model/embedding choices and hardware sizing remain
REQUIRES RESEARCH. None blocking the platform, which runs on the general model + RAG.

## Next-phase prerequisites
Phase 05 (Cyber Intelligence) builds on the delivered platform (RAG + gateway + domain services);
Dula AI iterations continue in parallel using this pipeline, shipping only when a candidate clears
the gate.

## Phase status
**Phase 04 — COMPLETE.** Implementation, tests, security validation, and documentation are done
and verified; a real candidate was trained, evaluated, and **retired** with the decision recorded.
Acceptance met on the retire outcome. Awaiting go-ahead for Phase 05.
