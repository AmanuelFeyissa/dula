---
title: AI Area — Overview
document_id: AI-000
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: AI
audience: AI/ML engineers, architects
phase: Documentation Bootstrap (M000)
---

# 08 — AI (Dula AI & Applied AI)

> **Purpose.** Entry point for the AI strategy: how we go from *using an open model* to
> *a specialized, evaluated, optimized Dula AI* — without pretending to train a foundation
> model from scratch on day one.

## Reading Order

1. [DulaAIStrategy.md](./DulaAIStrategy.md) — the staged progression and when each stage
   is justified.
2. [ModelSelection.md](./ModelSelection.md) — choosing base models.
3. [DatasetStrategy.md](./DatasetStrategy.md) + [DataPipeline.md](./DataPipeline.md) — data.
4. [RAGEngineering.md](./RAGEngineering.md) — retrieval grounding.
   [CyberIntelligence.md](./CyberIntelligence.md) — CTI extraction, vulnerability analysis,
   detection authoring (Phase 05, CURRENT).
5. [FineTuningStrategy.md](./FineTuningStrategy.md) + [TrainingStrategy.md](./TrainingStrategy.md)
   — adaptation.
6. [EvaluationStrategy.md](./EvaluationStrategy.md) + [Benchmarking.md](./Benchmarking.md)
   — measuring quality (gates everything).
7. [InferenceArchitecture.md](./InferenceArchitecture.md) + [ModelOptimization.md](./ModelOptimization.md)
   — serving.
8. [AIResearchRoadmap.md](./AIResearchRoadmap.md) — longer-term.

## Cross-Area Links

- Architecture spine: [../03-Architecture/AIArchitecture.md](../03-Architecture/AIArchitecture.md)
- Operationalization: [../09-MLOps/README.md](../09-MLOps/README.md)
- AI security: [../10-Security/AIThreatModel.md](../10-Security/AIThreatModel.md)

## Core Stance

- **Evaluation gates everything.** No model or prompt change ships without measured,
  non-regressing quality on the internal benchmark.
- **Grounding over recall.** Prefer RAG + tools to memorized facts.
- **Offline-first.** Everything must be runnable air-gapped with local models.
