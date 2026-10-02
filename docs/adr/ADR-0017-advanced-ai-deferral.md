# ADR-0017: Advanced-AI Directions Deferred — Adaptation Has Not Beaten the Incumbent

- Status: Accepted
- Date: 2026-10-02
- Deciders: AI, Architecture, Security (business sign-off: project owner)
- Related: [ADR-0007](./ADR-0007-base-model.md), [ADR-0010](./ADR-0010-mlops-tooling.md), [ADR-0012](./ADR-0012-training-and-hosting.md), [../08-AI/EvaluationStrategy.md](../08-AI/EvaluationStrategy.md), [../08-AI/AIResearchRoadmap.md](../08-AI/AIResearchRoadmap.md), [../04-MVP-Roadmap/Phase11-AdvancedAI.md](../04-MVP-Roadmap/Phase11-AdvancedAI.md)

## Context

Phase 11 (Advanced AI) is **trigger-gated research**: DPO/RLAIF preference optimization,
distillation, task-specialized small models, and continued/from-scratch pretraining are pursued
**only when measured evidence shows that adaptation has plateaued below the incumbent and a
business case exists** ([Phase11-AdvancedAI.md](../04-MVP-Roadmap/Phase11-AdvancedAI.md); its
Definition of Done states that "unjustified directions are explicitly **not** pursued"). The
incumbent is the shipped Dula AI configuration: a permissive general base model
(`Qwen/Qwen2.5-7B-Instruct`, ADR-0007) behind the LLM Gateway, grounded by RAG, with the
platform's deterministic cyber-intelligence tooling (`dula_ai.intel`) for detection authoring,
IOC/ATT&CK extraction, and validation.

This ADR records the evidence gathered across Phases 04, 10, and the 2026-09 evaluation overhaul,
and the decision that follows from it, so a future contributor does not re-open speculative
training without new evidence.

### Measured evidence

Three fine-tuning candidates were built, evaluated, and **retired** by the gate
(`ml/registry/registry.jsonl`), each regressing safety relative to its own untuned base despite
a DPO safety-restoration pass:

| Candidate | Base | Method | Outcome |
|-----------|------|--------|---------|
| v0.1 | Qwen2.5-0.5B-Instruct | QLoRA | retired (safety regression) |
| v0.2 | Qwen2.5-3B-Instruct | QLoRA (Modal) | retired (quality +0.02 but safety 1.00→0.75) |
| v0.3 | Qwen2.5-7B-Instruct | QLoRA + DPO (Kaggle) | retired (quality 0.82 vs 0.84; safety 0.75 vs 1.00) |

Because the first three evaluations used weak instruments (a small multiple-choice set plus four
refusal prompts), a measurement-first **Stage 1** pass rebuilt the gate to score the skills Dula
AI is meant to add (`dula_ml.tasks`: Sigma/YARA validity, IOC and ATT&CK extraction P/R/F1,
log-triage) and expanded the safety suite to 44 labelled prompts (adversarial-must-refuse plus
benign-must-comply, so over-refusal is also measured). The **stock 7B base** was then scored on
all suites (Kaggle, ~10 GPU-min):

| Suite | Stock base |
|-------|-----------|
| Safety refusal (30 adversarial) | 0.93 |
| Over-refusal (14 benign) | 0.00 |
| YARA authoring | 1.00 |
| Log triage | 1.00 |
| IOC extraction (F1) | 0.94 |
| Knowledge MCQ | 0.80 |
| ATT&CK mapping (F1) | 0.56 (understated — strict single-answer gold vs defensible extra techniques) |
| Sigma authoring | 0.00 valid / 0.875 content |

The base model is strong across every capability except **Sigma rule validity**, and inspection
of the raw outputs showed that gap is a *format* defect — the base knows the detection content
but emits non-spec top-level keys (`name`/`log_source` instead of `title`/`logsource`). That gap
is closed deterministically in the **platform layer** (`dula_ai.intel.detections.sigma.normalize_text`
corrects the keys; `build_ioc_rule` was already guaranteed-valid), not by training.

## Options Considered

1. **Pursue a fourth fine-tune (stronger DPO / task-specialized SFT) anyway.** Rejected: every
   measured candidate has lost safety relative to its base, the incumbent already matches or beats
   the best candidate on quality, and the one real gap is a formatting convention the platform
   solves without touching weights. Training to fix it would spend GPU and reintroduce the
   safety-regression risk to buy nothing the platform does not already provide — a direct
   violation of the evaluation gate and of Phase 11's own DoD.
2. **Distillation / task-specialized small models now.** Rejected: there is no better teacher than
   the incumbent to distil from, and the narrow tasks (IOC/ATT&CK extraction, triage) are already
   handled at 0.94–1.00 by the base plus deterministic tooling; a small model would have to beat
   that to ship, which the evidence makes implausible.
3. **Continued or from-scratch pretraining.** Rejected: explicitly RESEARCH/"likely never" in the
   strategy, with no licensing/sovereignty trigger met and no funded business case.
4. **Defer all advanced-AI directions, record the evidence and the concrete conditions that would
   re-open them, and keep the evaluation harness + staged artifacts ready.** Chosen.

## Decision

**Advanced-AI training directions are deferred, not pursued, as of this ADR.** Dula AI ships as
the general base model + RAG + the platform's deterministic cyber-intelligence tooling. The
decision is data-driven and reversible: the evaluation harness (`dula_ml.tasks` +
`dula_ml.evaluation` + `ml/runners/kaggle`), the held-out benchmark, and the staged SFT adapter
(`hf://AmanuelFeyissa/dula-ai-staging/v0.3-sft`) remain in place so any future candidate can be
judged by the same gate without rebuilding the pipeline.

A Phase 11 direction is re-opened **only** when all of the following hold (per
[AIResearchRoadmap.md](../08-AI/AIResearchRoadmap.md) §2 triggers):

- **A measured ceiling.** A current, held-out benchmark shows the incumbent (base + RAG +
  platform tooling) scoring below an agreed task threshold on a capability that adaptation could
  plausibly improve — not trivia, but a shipped use case.
- **A candidate that clears the gate.** A quarantined candidate **beats the incumbent on the task
  suite with no safety-refusal regression and no over-refusal growth** (`dula_ml.evaluation.decide`).
- **A business case.** The capability is high-volume or high-value enough to justify the training,
  serving, and maintenance cost, and (for pretraining) the licensing/sovereignty or funding
  trigger is met.

Any adopted direction gets its own ADR, model card, dual-use safety review
([../10-Security/AIThreatModel.md](../10-Security/AIThreatModel.md)), and registry entry.

## Consequences

- **Positive**: the platform ships on a strong, safe, well-understood configuration; no GPU spend
  or safety risk is incurred for capabilities the incumbent already provides; the "evaluation
  gates everything" principle is upheld rather than overridden to force a training outcome.
- **Positive**: the decision is auditable and reversible — the evidence, the harness, and the
  re-trigger criteria are all recorded, so a future contributor with new evidence can re-open a
  direction cleanly instead of re-litigating from scratch.
- **Negative / accepted**: Dula AI remains an *adaptation + tooling* product rather than a bespoke
  fine-tuned model for now. This is the honest reading of the evidence, not a capability the
  evidence says we are missing.
- **Neutral**: Phase 11 closes as a documented research outcome (deferral), which is an explicit,
  valid Definition of Done for a trigger-gated research phase — not an incomplete milestone.

## Compliance / Verification

- Evidence is reproducible: `ml/registry/registry.jsonl` (the three retirements and their cards),
  `ml/evaluation/benchmark_seed.json` (the held-out suite), and the Stage 1 baseline run on
  Kaggle (`ml/runners/kaggle`, `--mode baseline`).
- The platform-layer resolution of the one real gap is covered by
  `packages/dula-ai/tests/test_intel_detections.py` (`normalize_text` corrects `name`/`log_source`
  and re-validates) and the deterministic `build_ioc_rule` tests.
- The gate that any future candidate must clear is unit-tested in
  `packages/dula-ml/tests/test_evaluation.py` (task-mean quality, knowledge tolerance, adversarial
  refusal, over-refusal).
