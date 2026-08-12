# services/

Backend domain/intelligence services (Product 1 — Dula Platform). See
[../docs/03-Architecture/ComponentArchitecture.md](../docs/03-Architecture/ComponentArchitecture.md).

- `llm-gateway/` — model-agnostic inference gateway *(Phase 03)*
- `rag-service/` — retrieval + indexing (Qdrant + OpenSearch) *(Phase 03)*
- `agent-runtime/` — LangGraph-based agent orchestration *(Phase 06)*
- `connectors/` — plugin/connector host *(Phase 07)*
