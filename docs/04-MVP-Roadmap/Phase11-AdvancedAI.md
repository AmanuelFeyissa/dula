---
title: Phase 11 — Advanced AI (Research)
document_id: MVP-011
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: AI Research
audience: All contributors
phase: Documentation Bootstrap (M000)
related:
  - ../08-AI/AIResearchRoadmap.md
  - ../08-AI/DulaAIStrategy.md
---

# Phase 11 — Advanced AI (Research)

> **Purpose.** Pursue higher-risk, higher-reward AI directions **only when justified** by
> measured ceilings and a business case. Everything here is **RESEARCH/EXPERIMENTAL** and
> gated by evaluation + safety.

## Objective
Advance Dula AI beyond adaptation where measured limits justify it: preference optimization,
distillation, task-specialized models, and (only if truly warranted) continued
pretraining — per [../08-AI/DulaAIStrategy.md](../08-AI/DulaAIStrategy.md) Stages 12–15.

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
