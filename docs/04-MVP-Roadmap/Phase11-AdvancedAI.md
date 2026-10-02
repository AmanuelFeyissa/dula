---
title: Phase 11 — Advanced AI (Research)
document_id: MVP-011
status: Accepted
version: 1.0.0
last_updated: 2026-10-02
owner: AI Research
audience: All contributors
phase: Phase 11 — Advanced AI (M012, closed — deferred)
related:
  - ../08-AI/AIResearchRoadmap.md
  - ../08-AI/DulaAIStrategy.md
  - ../adr/ADR-0017-advanced-ai-deferral.md
  - ./closure/M012-AdvancedAI-Closure.md
  - ./closure/Phase11-AdvancedAI-Completion-Review.md
---

# Phase 11 — Advanced AI (Research)

> **Purpose.** Pursue higher-risk, higher-reward AI directions **only when justified** by
> measured ceilings and a business case. Everything here is **RESEARCH/EXPERIMENTAL** and
> gated by evaluation + safety.

## Objective
Advance Dula AI beyond adaptation where measured limits justify it: preference optimization,
distillation, task-specialized models, and (only if truly warranted) continued
pretraining — per [../08-AI/DulaAIStrategy.md](../08-AI/DulaAIStrategy.md) Stages 12–15.

## Outcome (M012, 2026-10-02) — DEFERRED, evidence-based

Phase 11's triggers were evaluated and are **not met**, so its directions are **deferred, not
pursued** — the valid Definition of Done for a trigger-gated research phase. The decision is
recorded in [ADR-0017](../adr/ADR-0017-advanced-ai-deferral.md) and closed in
[M012 Closure](./closure/M012-AdvancedAI-Closure.md) /
[Phase 11 Completion Review](./closure/Phase11-AdvancedAI-Completion-Review.md).

Evidence: three fine-tuning candidates (v0.1–v0.3) were built and **retired** by the gate, each
regressing safety versus its own base; a measurement-first evaluation overhaul then scored the
**stock base** strongly on every shipped capability (safety-refusal 0.93 / over-refusal 0.00,
YARA 1.00, triage 1.00, IOC-F1 0.94, knowledge 0.80) with the one real gap — Sigma rule *validity*
— closed deterministically in the platform layer, not by training. No advanced-AI direction
currently beats the incumbent at acceptable cost and safety, so none is pursued. The evaluation
harness, held-out benchmark, and staged SFT adapter remain in place; a direction re-opens only on
the measured conditions in ADR-0017 and [../08-AI/AIResearchRoadmap.md](../08-AI/AIResearchRoadmap.md) §2.

## Scope (candidate, trigger-gated)
- DPO/RLAIF preference optimization.
- Distillation to small fast models.
- Task-specialized small models (classify/extract).
- Continued domain pretraining (RESEARCH).
- From-scratch pretraining (RESEARCH, likely never — only if licensing/sovereignty cannot
  be met otherwise).

## Dependencies
- Phase 10 (MLOps at scale); clear, measured evidence that adaptation has plateaued
  ([../08-AI/EvaluationStrategy.md](../08-AI/EvaluationStrategy.md)).

## Deliverables
- Only what passes the eval+safety gate and beats the incumbent at acceptable cost; each
  direction quarantined until promoted.

## Implementation Requirements
- Reproducible research pipelines; strict contamination control; safety re-eval.

## Tests
- Full benchmark + adversarial safety; regression-blocking gates.

## Security Requirements
- Dual-use safety review mandatory for any capability increase
  ([../10-Security/AIThreatModel.md](../10-Security/AIThreatModel.md)).

## Documentation
- Research notes, model cards, ADRs for any adopted direction; update PROJECT_STATE.

## Acceptance Criteria
- Any promoted artifact beats the incumbent on the benchmark with no safety regression and
  a justified cost/benefit.

## Definition of Done
- Global DoD + above; unjustified directions are explicitly **not** pursued.
