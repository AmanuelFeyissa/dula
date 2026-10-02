---
title: Milestone Closure — M012 (Advanced AI)
document_id: MVP-M012-CLOSURE
status: Reviewed
version: 1.0.0
last_updated: 2026-10-02
owner: Engineering
audience: Project Maintainer, Developer, Architect, ML Engineer, Security Engineer
phase: Phase 11 — Advanced AI (M012)
related:
  - ../../adr/ADR-0017-advanced-ai-deferral.md
  - ../Phase11-AdvancedAI.md
  - ../../08-AI/EvaluationStrategy.md
  - ../../08-AI/AIResearchRoadmap.md
  - ../../08-AI/DulaAIStrategy.md
  - ../../PROJECT_STATE.md
  - ./Phase11-AdvancedAI-Completion-Review.md
  - ./README.md
---

# Milestone Closure — M012 (Advanced AI)

> Produced per **CLAUDE.md §11.8**. M012 is Phase 11 (1:1, like every phase since M001), so this
> closure is paired with a
> [Phase 11 Completion Review](./Phase11-AdvancedAI-Completion-Review.md) per §11.9.

- **Milestone identifier:** M012
- **Milestone name:** Advanced AI (Research)
- **Objective:** Evaluate Phase 11's trigger-gated advanced-AI directions (DPO/RLAIF,
  distillation, task-specialized small models, continued/from-scratch pretraining) against the
  incumbent and pursue **only** what beats it on quality with no safety regression at justified
  cost — per [Phase11-AdvancedAI.md](../Phase11-AdvancedAI.md).
- **Scope:** decision + evidence only. No new training was warranted (see below); the
  milestone's deliverables are the recorded decision ([ADR-0017](../../adr/ADR-0017-advanced-ai-deferral.md)),
  the re-trigger criteria, and the finalization of the MVP roadmap. The evaluation overhaul that
  produced the deciding evidence (`dula_ml.tasks`, the expanded safety suite, the Kaggle
  `baseline` mode) shipped in the 2026-09-20 commits recorded in `PROJECT_STATE.md`.

## Implemented functionality

Phase 11 is trigger-gated research; its Definition of Done explicitly includes **not** pursuing
unjustified directions. M012 is therefore a **decision milestone**, and the "implementation" is
the evidence-gathering and the recorded decision:

- **Measurement-first evaluation (prerequisite, shipped 2026-09-20).** `dula_ml.tasks` scores the
  skills Dula AI is meant to add (Sigma/YARA structural validity + required content, IOC and
  ATT&CK extraction precision/recall/F1, log-triage MCQ); `dula_ml.evaluation.decide` gates on
  mean task score, a knowledge-accuracy tolerance, adversarial refusal, and over-refusal; the
  held-out seed grew to 44 safety prompts (30 refuse / 14 benign-must-comply) + 36 task items; the
  Kaggle kernel gained a `baseline` mode.
- **Baseline measurement.** The stock `Qwen/Qwen2.5-7B-Instruct` scored 0.93 adversarial refusal /
  0.00 over-refusal, YARA 1.00, triage 1.00, IOC-F1 0.94, knowledge 0.80, ATT&CK-F1 0.56
  (understated), Sigma validity 0.00 (content 0.875 — a format defect).
- **Platform-layer resolution of the one real gap.** `dula_ai.intel.detections.sigma.normalize_text`
  corrects the non-spec keys a general model emits (`name`→`title`, `log_source`→`logsource`) and
  re-validates; `build_ioc_rule` was already guaranteed-valid.
- **Decision.** [ADR-0017](../../adr/ADR-0017-advanced-ai-deferral.md): advanced-AI directions are
  **deferred, not pursued**, with explicit, measurable re-trigger criteria; the eval harness,
  benchmark, and staged SFT adapter are kept ready.

## Technical changes

None beyond the already-merged evaluation overhaul and the Sigma normalizer (both pre-M012
closure, recorded in `PROJECT_STATE.md`). No new model, training run, or serving path was added —
by design.

## Architecture changes

One new Accepted ADR ([ADR-0017](../../adr/ADR-0017-advanced-ai-deferral.md)). No structural code
change.

## Database changes

None.

## API changes

None.

## Security changes

None introduced. The decision **avoids** a safety regression: every measured fine-tune lost
adversarial-refusal relative to its base, so declining to ship one preserves the incumbent's
0.93/0.00 refusal/over-refusal posture. Any future re-opened direction requires a dual-use safety
review per [AIThreatModel.md](../../10-Security/AIThreatModel.md).

## AI/ML changes

Dula AI is confirmed to ship as the general base model + RAG + deterministic cyber-intelligence
tooling. No new weights.

## Testing performed

- `dula_ml` gate + task scorers: `packages/dula-ml/tests/test_evaluation.py`,
  `test_tasks.py` (IOC gold labels self-verified recoverable; gate covers task-mean, knowledge
  tolerance, refusal, over-refusal).
- Sigma normalization: `packages/dula-ai/tests/test_intel_detections.py`.
- Full suite green at closure (`uv run pytest --ignore=apps/worker` → all passed; with the local
  stack up, the Postgres-dependent suite runs too: 342 passed / 0 skipped on 2026-10-02).

## Security validation performed

Decision reviewed against the evaluation + safety gate; no capability increase shipped, so no new
dual-use surface. The retirement evidence itself is the safety validation: candidates that
regressed refusal were not shipped.

## Deployment validation

Not applicable (no deployable artifact). Separately on 2026-10-02 the platform was stood up
locally end to end (Docker Compose stack + both API services) and the Helm chart was validated
against a live Kubernetes API across all four profiles (kind) — recorded in `PROJECT_STATE.md`.

## Documentation completed

### Documentation Impact Assessment (CLAUDE.md §11.6)

1. **Functionality implemented:** a recorded, evidence-based decision to defer advanced-AI
   directions; no runtime functionality.
2. **Technical docs created:** [ADR-0017](../../adr/ADR-0017-advanced-ai-deferral.md); this closure;
   the [Phase 11 Completion Review](./Phase11-AdvancedAI-Completion-Review.md).
3. **Technical docs updated:** [Phase11-AdvancedAI.md](../Phase11-AdvancedAI.md) (Outcome +
   status), [AIResearchRoadmap.md](../../08-AI/AIResearchRoadmap.md) (preference-optimization
   trigger marked evaluated/not-met), `PROJECT_STATE.md`, `PROJECT_CONTEXT.md`, `docs/SUMMARY.md`,
   `CLAUDE.md` (ADR index).
4. **User docs created:** none — nothing user-facing changed (Dula AI already ships as the general
   model + RAG; the user guides for Ask/Intel/Agents remain accurate).
5. **User docs updated:** none required.
6. **Intentionally not created:** training/model/RAG/agent/plugin/API/DB/deployment docs — no such
   artifact was produced this milestone (N/A, by the deferral decision).
7. **Examples/commands verified:** the reproducibility pointers in ADR-0017 (registry, benchmark
   seed, Kaggle `--mode baseline`) match the code.
8. **Links valid:** verified (`tools/check-doc-links.sh` / §9 link check).
9. **Diagrams:** none required.
10. **Incomplete items:** none.
11. **Known documentation gaps:** none.

### Milestone Documentation Checklist (CLAUDE.md §11.7)

#### Technical Documentation
- [x] Architecture updated (ADR-0017)
- [N/A] API documentation — no API change
- [N/A] Database documentation — no DB change
- [N/A] Configuration — no config change
- [x] Security documentation — decision records the safety rationale; AIThreatModel referenced
- [N/A] Deployment documentation — no deployable artifact
- [x] Testing documentation — gate/scorer tests described
- [N/A] Troubleshooting — nothing new to operate
- [N/A] Operational/runbook — the training runbook is unchanged and still accurate
- [x] AI/ML documentation updated (AIResearchRoadmap, Phase 11 Outcome)
- [N/A] RAG / Agent / Plugin — unchanged

#### User Documentation
- [N/A] Getting Started / Installation / Configuration / User / Admin / Operator / Feature /
  Troubleshooting / FAQ — nothing user-facing changed this milestone.

#### Documentation Quality
- [x] Front matter follows DocumentationStandards.md
- [x] Naming follows NamingConventions.md
- [x] Relative links validated
- [N/A] Mermaid diagrams
- [x] Commands verified (reproducibility pointers)
- [N/A] Configuration / API examples
- [x] No undocumented implemented functionality
- [x] No implemented functionality incorrectly marked FUTURE
- [x] No future functionality presented as CURRENT
- [x] Added to docs/SUMMARY.md
- [x] Glossary terms — no new terms
- [x] PROJECT_CONTEXT.md updated
- [x] PROJECT_STATE.md updated

## Known limitations

Dula AI remains an adaptation + tooling product, not a bespoke fine-tuned model. This reflects the
evidence, not an unmet need. The task benchmark is intentionally small (illustrative held-out
suite + MMLU `computer_security`); a larger expert-authored benchmark would sharpen any future
re-trigger decision (noted as the natural first step if Phase 11 ever re-opens).

## Known issues

None.

## Deferred work

All Phase 11 directions (DPO/RLAIF, distillation, task-specialized models, continued/from-scratch
pretraining) are deferred under the measurable re-trigger criteria in ADR-0017. Non-AI backlog
unaffected by this milestone and still open: operational GA acceptance (real cluster + pen test +
DR drill), durable trigger store + bus-fed event triggers, container sandbox runner, Terraform +
Argo CD, cluster-scale load test — all tracked in `PROJECT_STATE.md`.

## Lessons learned

- **Measure before you train.** The first three candidates were judged on instruments too weak to
  see task skill or distinguish safety; rebuilding the gate first (Stage 1) changed the decision
  from "keep trying" to "the base is already good enough," saving further GPU spend.
- **Some gaps belong in the platform, not the weights.** The one real deficiency (Sigma key
  naming) was fixed deterministically and safely in `dula_ai.intel`, which no fine-tune could have
  done more reliably.
- **A research phase can legitimately conclude "not yet."** Recording the evidence and the
  re-trigger conditions is a real deliverable, not an absence of one.

## Next milestone

None in the MVP roadmap — M012 completes Phases 01–11. Future work is the non-blocking backlog in
`PROJECT_STATE.md`, pursued on explicit direction (and advanced AI only on an ADR-0017 trigger).

## Documentation gaps

None blocking closure.

## Final status

- **COMPLETE.** Phase 11's trigger gate was evaluated with reproducible evidence; the decision to
  defer advanced-AI directions is recorded in Accepted ADR-0017 with measurable re-open criteria;
  required technical documentation exists and is verified; no user documentation was required; and
  `PROJECT_STATE.md` / `PROJECT_CONTEXT.md` are updated. Deferral is the explicit, valid Definition
  of Done for a trigger-gated research phase — not a documentation gap.
