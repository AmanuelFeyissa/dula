---
title: RAG Runbook
document_id: OPS-007
status: Draft
version: 0.1.0
last_updated: 2026-08-12
owner: DevOps/SRE, AI
audience: Operator, DevOps/SRE, AI Engineer
phase: Phase 03 — Knowledge & RAG (M003)
related:
  - ../03-Architecture/RAGArchitecture.md
  - ../08-AI/RAGEngineering.md
  - ../08-AI/KnowledgeSources.md
  - ../12-API/AIGatewayAPI.md
---

# RAG Runbook

> **Purpose.** Operate the Dula RAG subsystem and AI Gateway: profiles, bring-up, knowledge
> lifecycle, and incident response (including poisoned-source purge). **Status: CURRENT.**

## Profiles

- **offline** (default): in-memory stores, hashing embedder, `extractive-v1` provider — no
  network, air-gapped. Answers are grounded and cited over the seeded public corpus.
- **backed**: Qdrant (vectors) + OpenSearch (BM25), optional Ollama serving.

Selected via `DULA_*`/settings env on `apps/ai-gateway` (see
[../12-API/AIGatewayAPI.md](../12-API/AIGatewayAPI.md)). No code change is needed to switch.

## Bring-up (local dev)

```bash
# Backed stores + local LLM serving (optional):
docker compose -f deploy/docker/docker-compose.dev.yml up -d qdrant opensearch opa
docker compose -f deploy/docker/docker-compose.dev.yml --profile ai up -d ollama
ollama pull llama3.1:8b            # only if provider=ollama

# Run the gateway (offline profile by default):
uv run uvicorn dula_ai_gateway.main:app --port 8100
```

Readiness: `GET /healthz` (liveness), `GET /readyz`.

## Knowledge lifecycle

- **Public knowledge** is seeded at startup (demo corpus) and, in production, ingested from
  registered sources with license checks — see
  [../08-AI/KnowledgeSources.md](../08-AI/KnowledgeSources.md).
- **Tenant-private knowledge** is ingested via `POST /api/v1/knowledge/documents` (scoped to
  the caller's tenant, never public).
- **Re-embedding:** changing the embedding model requires re-ingesting/re-embedding; the
  embedding model name is recorded on every chunk (`metadata.embedding_model`).

## Incident: suspected RAG poisoning (T3)

1. Identify the offending `source` (chunks carry `source` + provenance metadata).
2. Purge it everywhere: `DELETE /api/v1/knowledge/sources/{source}` (removes from vector +
   lexical indices).
3. Re-ingest from a trusted snapshot; verify with the evaluation benchmark.

## Incident: cross-tenant retrieval concern (T14)

- Retrieval filters to `{tenant, public}` **at query time** in both stores. To verify, run
  the tenant-isolation tests (`packages/dula-ai/tests/test_retrieval.py`) and the gateway
  isolation test (`apps/ai-gateway/tests/test_ask.py`).

## Incident: token-budget exhaustion / denial of wallet (T15)

- Per-tenant token budgets are enforced at the gateway; exhaustion returns **429**. Raise
  `max_tokens_per_tenant` deliberately, or investigate the abusive tenant via the
  `ai.query.completed` audit events.

## Quality gate

- The RAG evaluation benchmark (recall/citations/groundedness) runs in CI
  ([../08-AI/Benchmarking.md](../08-AI/Benchmarking.md)); a regression below baseline blocks
  release. Never ship a RAG/prompt/model change that drops the benchmark.

## Observability

- Every AI call logs structured audit metadata (no prompt/answer content) and emits an
  `ai.query.completed` event. Watch token totals, `cached` ratio, and `input_flags`
  (possible injection attempts).
