---
title: Phase 11 Completion Review — Advanced AI (and MVP Roadmap Finalization)
document_id: MVP-P11-REVIEW
status: Reviewed
version: 1.0.0
last_updated: 2026-10-02
owner: Engineering
audience: Project Maintainer, Architect, ML Engineer, Security Engineer, DevOps/SRE
phase: Phase 11 — Advanced AI (M012)
related:
  - ./M012-AdvancedAI-Closure.md
  - ../Phase11-AdvancedAI.md
  - ../../adr/ADR-0017-advanced-ai-deferral.md
  - ../../08-AI/AIResearchRoadmap.md
  - ../MVPOverview.md
  - ../../PROJECT_STATE.md
  - ../../PROJECT_CONTEXT.md
  - ./README.md
---

# Phase 11 Completion Review — Advanced AI

> Produced per **CLAUDE.md §11.9**. Phase 11 is the final phase of the MVP roadmap, so this review
> also finalizes the roadmap: every phase (01–11) now has a milestone closure and a completion
> review in this folder.

## Phase objective

Pursue higher-risk, higher-reward AI directions **only when justified** by a measured ceiling and a
business case, gated by evaluation + safety. Decide, with evidence, whether to advance Dula AI
beyond adaptation.

## Milestones completed

- **M012 — Advanced AI.** [Closure](./M012-AdvancedAI-Closure.md). Outcome: advanced-AI directions
  **deferred** per [ADR-0017](../../adr/ADR-0017-advanced-ai-deferral.md) — the valid Definition of
  Done for a trigger-gated research phase.

## Features delivered

- A measurement-first evaluation capability that scores Dula AI on real task skill
  (`dula_ml.tasks`) and a meaningful safety suite (adversarial refusal **and** over-refusal), with
  a gate (`dula_ml.evaluation.decide`) any future candidate must clear.
- A reproducible baseline measurement of the incumbent, establishing that the general base + RAG +
  deterministic tooling already meets the shipped capabilities.
- A platform-layer fix (`sigma.normalize_text`) for the single real model gap found, so detection
  authoring is spec-valid without training.
- The recorded, reversible decision (ADR-0017) with measurable re-trigger criteria.

No new model weights, training pipeline, or serving path were delivered — intentionally, because
none cleared the gate at acceptable cost and safety.

## Architecture delivered

One Accepted ADR (ADR-0017). No new runtime components. The two-product boundary (Dula Platform /
Dula AI) is unchanged; Dula AI remains model-agnostic behind the LLM Gateway (ADR-0005/0007).

## Security posture

Preserved and, in effect, protected: declining to ship a fine-tune keeps the incumbent's measured
0.93 adversarial-refusal / 0.00 over-refusal posture, rather than accepting the refusal regression
every candidate showed. Any future re-opened direction carries a mandatory dual-use safety review
([../../10-Security/AIThreatModel.md](../../10-Security/AIThreatModel.md)). Defensive-only scope is
intact.

## Testing status

Full suite green at closure: `uv run pytest --ignore=apps/worker` all passed; with the local stack
running, the Postgres-dependent suite executes too (342 passed / 0 skipped, 2026-10-02). The gate
and task scorers, and the Sigma normalizer, are unit-tested. CI (ruff, mypy-strict, pytest, Helm
lint + kubeconform) green on every push.

## Documentation status

Complete for the phase: ADR-0017, M012 closure, this review, the Phase 11 Outcome section, and the
AIResearchRoadmap trigger update. Links, naming, and front matter verified.

## User-documentation status

No change required — nothing user-facing changed this phase. The existing user guides
(`docs/17-User-Documentation/`) remain accurate for the shipped Dula AI (general model + RAG +
intel tooling).

## Known limitations

- Dula AI is an adaptation + tooling product, not a bespoke fine-tuned model (by evidence, not by
  gap).
- The task benchmark is deliberately small; a larger expert-authored suite is the natural first
  step if Phase 11 is ever re-opened.

## Technical debt

None introduced by this phase. Pre-existing, non-blocking items remain tracked in
`PROJECT_STATE.md` (see Deferred items).

## Deferred items

- **Advanced-AI directions** (DPO/RLAIF, distillation, task-specialized models, continued/from-
  scratch pretraining) — deferred under ADR-0017's measurable re-trigger criteria.
- **Operational GA acceptance** — live deploy across all four profiles on real infrastructure, an
  external penetration test, and a DR restore drill (RPO/RTO). Owned by the deploying team; needs a
  real cluster and a cloud-budget decision.
- **Platform backlog** — durable Postgres trigger store + bus-fed event triggers; container sandbox
  runner + third-party plugin loader; Terraform IaC + GitOps (Argo CD); cluster-scale telemetry /
  worker load test; embedding/reranker model + hardware sizing.

## Lessons learned

- Rebuilding the evaluation instruments **before** spending more GPU converted an open-ended "keep
  fine-tuning" into a clear, evidence-based stop.
- Fixing a capability gap in deterministic platform code can be safer and more reliable than
  training for it.
- A research phase closing as a documented, reversible "not yet" is a legitimate, complete outcome.

## Outstanding risks

- If a future, larger benchmark reveals a real capability ceiling, the deferral must be revisited
  (ADR-0017 triggers). Low near-term risk given the current evidence.
- The GA-acceptance items remain gated on real infrastructure; the platform is buildable and
  locally verified, but a production sign-off still requires a live environment.

## Next-phase prerequisites

None within the MVP roadmap — Phases 01–11 are complete. Any further work is the non-blocking
backlog above, undertaken on explicit direction, with advanced AI gated by ADR-0017.

## MVP roadmap finalization

With M012 closed, all eleven phases have a closure report and a completion review in this folder,
and `PROJECT_STATE.md` reflects the full MVP as delivered (buildable scope) with the two products —
**Dula Platform** and **Dula AI** — complete to their defined MVP. Remaining work is operational
acceptance on real infrastructure and the explicitly-deferred backlog, not unfinished MVP scope.
