---
title: RAG Engineering
document_id: AI-007
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: AI
audience: AI/ML engineers
phase: Documentation Bootstrap (M000)
related:
  - ../03-Architecture/RAGArchitecture.md
  - ./EvaluationStrategy.md
  - ../10-Security/AIThreatModel.md
---

# RAG Engineering

> **Purpose.** The engineering detail behind the RAG architecture: chunking, embeddings,
> hybrid search, reranking, context assembly, and evaluation. Architecture view:
> [../03-Architecture/RAGArchitecture.md](../03-Architecture/RAGArchitecture.md).

## 1. Chunking

- Structure-aware chunking (respect sections, rules, tables); target chunk sizes tuned
  per source type; overlap to preserve context. Exact sizes **REQUIRES RESEARCH** and are
  tuned via retrieval eval.
- Attach metadata to each chunk: source, license, tenant, classification, timestamp,
  version, ATT&CK/CVE identifiers where applicable.

## 2. Embeddings

- Use open, self-hostable embedding models (bge/e5/gte families are candidates —
  **REQUIRES RESEARCH**, ADR-0007 scope) so RAG runs offline.
- Embedding model version is recorded; changing it requires **re-embedding** (pipeline
  step) — a migration concern tracked in [../03-Architecture/ArchitectureRoadmap.md](../03-Architecture/ArchitectureRoadmap.md).

## 3. Hybrid Retrieval

- Combine vector similarity with BM25 (OpenSearch); fuse scores (e.g. reciprocal rank
  fusion). Hybrid consistently improves recall over vector-only for security jargon/IDs.

## 4. Filtering & Authorization

- Apply tenant + authorization + classification filters **at retrieval time**, before
  content reaches the model (prevents cross-tenant/unauthorized leakage) —
  [../03-Architecture/RAGArchitecture.md](../03-Architecture/RAGArchitecture.md).

## 5. Reranking

- Optional cross-encoder/model reranker for precision; cost/latency trade-off evaluated.
  Specific reranker **REQUIRES RESEARCH**.

## 6. Context Assembly & Prompting

- Assemble top-k reranked chunks with citations; clearly delimit **untrusted retrieved
  content** from system instructions (prompt-injection defense —
  [../10-Security/AIThreatModel.md](../10-Security/AIThreatModel.md)).
- Enforce citation in outputs for grounded tasks; unsupported claims are flagged.

## 7. Evaluation

- Metrics: retrieval recall/precision@k, answer groundedness, citation correctness,
  hallucination rate. Continuous eval per
  [./EvaluationStrategy.md](./EvaluationStrategy.md) and
  [../15-Testing/AIEvaluation.md](../15-Testing/AIEvaluation.md).

## 8. Freshness

- Re-index on source updates (CVEs/advisories change frequently); track index version so
  answers can cite the knowledge snapshot used.

## Related Documents

- [../03-Architecture/RAGArchitecture.md](../03-Architecture/RAGArchitecture.md) ·
  [./DataPipeline.md](./DataPipeline.md)
