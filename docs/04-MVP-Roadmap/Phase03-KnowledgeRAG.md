---
title: Phase 03 — Knowledge & RAG (First Usable MVP)
document_id: MVP-003
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: AI / Backend
audience: All contributors
phase: Documentation Bootstrap (M000)
related:
  - ../03-Architecture/RAGArchitecture.md
  - ../08-AI/RAGEngineering.md
---

# Phase 03 — Knowledge & RAG  ⭐ First Usable MVP

> **Purpose.** Deliver the first genuinely useful capability: grounded, cited security
> Q&A and alert triage on a **general open model** — value before Dula AI exists.

## Objective
Stand up the LLM gateway + local model serving, the RAG subsystem, and deliver UC-01
(triage) and UC-14 (grounded Q&A) with citations.

## Scope
- LLM gateway + local serving (vLLM/llama.cpp) ([../03-Architecture/AIArchitecture.md](../03-Architecture/AIArchitecture.md)).
- RAG: indexing + hybrid retrieval + citations ([../08-AI/RAGEngineering.md](../08-AI/RAGEngineering.md));
  **vector store = Qdrant; lexical/BM25 + log-analytics = OpenSearch** — hybrid retrieval
  stood up in its permanent form from this phase (ADR-0003).
- Ingest public knowledge (ATT&CK/CVE/etc.) with license checks
  ([../08-AI/DatasetStrategy.md](../08-AI/DatasetStrategy.md)).
- Initial **evaluation benchmark** (Stage 6) — built here, before any tuning
  ([../08-AI/Benchmarking.md](../08-AI/Benchmarking.md)).
- UI: chat/triage views with streaming + evidence.

## Dependencies
- Phase 02 complete.

## Deliverables
- Analyst can ask questions / triage an alert and get grounded, cited answers; benchmark
  runs and produces a baseline.

## Implementation Requirements
- Untrusted-content handling & guardrails ([../10-Security/AIThreatModel.md](../10-Security/AIThreatModel.md));
  retrieval-time authZ/tenant filtering.

## Tests
- RAG evaluation (recall/groundedness/citations); AI red-team basics (injection);
  UC-01/UC-14 E2E ([../15-Testing/AIEvaluation.md](../15-Testing/AIEvaluation.md)).

## Security Requirements
- Prompt-injection defenses; no cross-tenant retrieval; no secrets in context; audit of AI
  calls.

## Documentation
- RAG runbook, knowledge-source registry, benchmark description; update PROJECT_STATE.

## Acceptance Criteria
- Grounded answers with correct citations on the benchmark above a baseline; injection
  red-team basics pass; works fully offline with local models.

## Definition of Done
- Global DoD + above; **this is the first shippable MVP** (general-model-powered).
