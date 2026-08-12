# ADR-0003: Vector Database & Search Engine

- Status: Accepted
- Date: 2026-08-11
- Revised: 2026-08-11 (M000 — promoted from "pgvector/Postgres-FTS for MVP → migrate later" to the permanent choices below; nothing was implemented under the prior staged wording)
- Deciders: Architecture, AI
- Related: [../03-Architecture/RAGArchitecture.md](../03-Architecture/RAGArchitecture.md)

## Context
RAG needs vector storage, and the platform needs lexical/full-text search plus
security-log analytics. The project is production-grade from the outset (not a throwaway
MVP), so the datastores are chosen as the permanent, scalable targets rather than starter
substitutes to be migrated later.

## Options Considered
- **Vector:** Qdrant (purpose-built ANN, Rust, Apache-2.0, rich filtering, air-gap
  friendly) vs pgvector (simplest, reuses Postgres, weaker at scale/filtering) vs
  Milvus/Weaviate (heavier/more opinionated).
- **Search/log-analytics:** OpenSearch (Apache-2.0, BM25 full-text + log analytics) vs
  PostgreSQL FTS (adequate for small corpora only) vs Elasticsearch (product-embedding
  license concerns) vs ClickHouse (analytics-oriented).

## Decision (permanent)
- **Vector database: Qdrant** — the platform's standard vector store from day one.
- **Search & log-analytics: OpenSearch** — the standard lexical/full-text engine (BM25)
  and security-log analytics store.
- **Hybrid retrieval = Qdrant (vectors) + OpenSearch (BM25)**, fused at query time.
- PostgreSQL remains the relational system of record; `pgvector` is **not** the platform
  vector store (it may be used only for incidental, non-RAG local needs).

## Consequences
- Production-grade recall, filtering, and log-analytics from the start; no later
  vector/search migration is planned.
- Slightly more infrastructure to stand up early (Qdrant + OpenSearch), accepted as the
  cost of a permanent architecture. The `rag-service` still abstracts the vector store so
  a future engine swap remains possible if a materially better technology emerges.

## Compliance / Verification
- No direct vector-store/search calls outside `rag-service`; hybrid retrieval uses both
  Qdrant and OpenSearch.
