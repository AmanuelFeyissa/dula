---
title: Milestone Closure — M003 (Phase 03 Knowledge & RAG)
document_id: MVP-M003-CLOSURE
status: Reviewed
version: 1.0.0
last_updated: 2026-08-12
owner: Engineering
audience: Project Maintainer, Developer, Architect, Security Engineer, ML Engineer, DevOps/SRE
phase: Phase 03 — Knowledge & RAG (M003)
related:
  - ../Phase03-KnowledgeRAG.md
  - ../../PROJECT_STATE.md
  - ./README.md
---

# Milestone Closure — M003

> Produced per **CLAUDE.md §11.8**.

- **Milestone identifier:** M003
- **Milestone name:** Phase 03 — Knowledge & RAG (First Usable MVP)
- **Objective:** Stand up the LLM Gateway + local model serving, the RAG subsystem, and deliver
  grounded cited Q&A (UC-14) and alert triage (UC-01) — value on a general model before Dula AI
  exists. See [../Phase03-KnowledgeRAG.md](../Phase03-KnowledgeRAG.md).
- **Scope:** LLM Gateway (model-agnostic, guardrails, budgets, audit); RAG (indexing, hybrid
  retrieval with tenant filtering, citations); knowledge ingestion with license checks; an
  evaluation benchmark; AI red-team basics; a chat/triage UI with streaming + evidence. Out of
  scope: a trained Dula AI model (Phase 04), fine-tuning, agents, full upstream-feed ingestion.

## Implemented functionality
- **`packages/dula-ai`** — the AI subsystem library:
  - LLM Gateway: pluggable providers (offline `extractive-v1` default; `OllamaProvider`),
    per-tenant token budgets (429), **per-tenant** response cache (never shared across tenants),
    output secret-redaction, token accounting, audit hook.
  - RAG: chunking (+provenance), embeddings (offline `HashingEmbedder`; `OllamaEmbedder`),
    stores (in-memory + **Qdrant** vectors + **OpenSearch** BM25), RRF **hybrid retrieval** with
    **tenant/relevance filtering at retrieval** + reranking, guardrails (injection detection,
    trust separation, citation enforcement), cited context assembly, knowledge ingestion with a
    **license allowlist** and source **purge**, an offline demo corpus, and a `build_offline_stack`
    factory.
- **`apps/ai-gateway`** — FastAPI service: `POST /api/v1/ask`, `POST /api/v1/ask/stream` (SSE),
  `POST /api/v1/triage`, `POST /api/v1/knowledge/documents`, `DELETE /api/v1/knowledge/sources/{s}`,
  health probes. OIDC auth + per-action OPA authorization (fail-closed), AI-call audit via log +
  `ai.query.completed` event.
- **OPA policy** expanded: `ai.ask`, `ai.triage` (all operational roles), `knowledge.ingest`
  (analyst/hunter/engineer), `knowledge.purge` (admin).
- **Web UI** — an **Ask** page (question + triage modes) with **SSE streaming** and an evidence
  list, served through server-side proxy routes that inject the token; nav link added.
- **Evaluation benchmark** (`test_eval_benchmark.py`) and **AI red-team** injection tests.
- **Dev stack**: optional Ollama service (opt-in `ai` profile).

## Technical / Architecture / Database / API / Security / AI-ML changes
- **Architecture:** the AI spine is realized — caller → LLM Gateway → (RAG retrieve) → provider →
  guardrails → cited answer. Model-agnostic; Dula AI (Phase 04) plugs in behind the gateway.
- **Database:** none (the AI Gateway is stateless; knowledge lives in Qdrant/OpenSearch or memory).
- **API:** new AI Gateway API ([../../12-API/AIGatewayAPI.md](../../12-API/AIGatewayAPI.md)).
- **Security (AIThreatModel.md):** untrusted-content handling (T2 indirect injection — trust
  separation, tested); tenant/authZ filtering at retrieval (T14/LLM08); no secrets in prompts,
  output secret-redaction (T5/T13); per-tenant budgets (T15); citation enforcement + relevance
  floor (T12 misinformation); fail-closed authZ; AI-call audit without prompt/answer content.
- **AI/ML:** offline RAG on a general model; **evaluation gates** the pipeline in CI.

## Testing performed
- `ruff` + `ruff format --check` clean; `mypy --strict` clean (56 source files; tests validated
  by ruff + pytest — excluded from the strict gate due to hyphenated package dirs).
- `pytest` **56 passed** (5 platform-api integration skip without a DB), incl. the RAG benchmark,
  gateway (budgets/cache-isolation/redaction), guardrails, knowledge/licensing, and injection
  red-team.
- **OPA policy tests 16/16** (`opa test`).
- `next build` (web) passes with the Ask UI + proxy routes.

## Security validation performed
- **No cross-tenant retrieval:** unit + gateway tests prove tenant B cannot retrieve tenant A's
  private knowledge (in-memory and **live Qdrant** payload filter).
- **Prompt injection:** direct-injection query flagged; indirect injection planted in a retrieved
  document is treated as data (system prompt never leaks; answer stays grounded/cited).
- **AuthZ:** denied action → 403 (fail-closed OPA client unit-tested); AI calls audited.
- **Budgets:** per-tenant token cap enforced (429).

## Deployment validation
- Offline profile runs with **no external dependencies** (Acceptance: works fully offline).
- **Live Qdrant** verified: ingest + tenant-filtered vector search against a running Qdrant.
- **Live OpenSearch verify — DEFERRED (environment):** the `opensearchproject/opensearch:2` image
  did not finish pulling on this constrained network. The adapter is code-complete and
  type-checked, and its BM25 behaviour is covered by the in-memory lexical store's unit tests; the
  full offline hybrid pipeline is tested end-to-end. To be re-run when the image is available.
- **K8s dev/staging deploy — DEFERRED** to the infrastructure phase (Helm/Argo CD, §10.3).

## Documentation Impact Assessment (CLAUDE.md §11.6)
1. **Implemented:** LLM Gateway, RAG, AI Gateway service, Ask/triage UI, benchmark, red-team.
2. **Technical docs created:** [AI Gateway API](../../12-API/AIGatewayAPI.md),
   [RAG Runbook](../../16-Operations/RAGRunbook.md),
   [Knowledge Source Registry](../../08-AI/KnowledgeSources.md); this closure + the Phase 03 review.
3. **Technical docs updated:** AIArchitecture, RAGArchitecture, RAGEngineering (status notes),
   Benchmarking (implemented baseline), 12-API/16-Operations/08-AI READMEs, SUMMARY, Glossary,
   PROJECT_STATE, PROJECT_CONTEXT.
4. **User docs created:** [Ask Dula User Guide](../../17-User-Documentation/AskDulaUserGuide.md).
5. **User docs updated:** 17-User-Documentation README (guide set + current state).
6. **Intentionally not created (N/A):** Model/training docs (Phase 04), Agent, Plugin — not built.
7. **Examples/commands verified:** API examples, benchmark, and live Qdrant flow executed.
8. **Links valid:** yes — `tools/check-doc-links.sh` passes.
9. **Diagrams:** existing Mermaid AI/RAG diagrams remain accurate.
10. **Incomplete items:** live OpenSearch/Ollama verification (environment), semantic embeddings.
11. **Known documentation gaps:** model/training user docs pending Phase 04.

## Milestone Documentation Checklist (CLAUDE.md §11.7)
### Technical
- [x] Architecture updated · [x] API documentation updated (AI Gateway API)
- [N/A] Database (stateless service) · [x] Configuration documented (profiles/settings)
- [x] Security documentation updated (threat mappings) · [x] Deployment updated (runbook/compose)
- [x] Testing documentation updated · [x] Troubleshooting (runbook + user guide)
- [x] Operational documentation updated (RAG runbook) · [x] AI/ML updated (RAG, benchmark, sources)
- [x] RAG documentation updated · [N/A] Agent · [N/A] Plugin/integration
### User
- [x] Feature documentation (Ask Dula guide) · [~] Getting Started (interim root README)
- [N/A] Installation · [~] Configuration (profiles in runbook) · [x] User guide (Ask Dula)
- [N/A] Administrator · [~] Operator (RAG runbook) · [x] Troubleshooting · [N/A] FAQ
### Quality
- [x] Front matter · [x] Naming · [x] Relative links validated · [x] Mermaid valid
- [x] Commands verified · [x] Config examples verified · [x] API examples verified
- [x] No undocumented implemented functionality · [x] No implemented-as-FUTURE
- [x] No FUTURE-as-CURRENT · [x] Added to SUMMARY.md · [x] Glossary terms added
- [x] PROJECT_CONTEXT.md updated · [x] PROJECT_STATE.md updated

## Known limitations / issues / deferred work
- **Offline default is not semantic:** the `HashingEmbedder` is lexical-ish; semantic quality
  needs a real embedding model (bge/e5/gte — REQUIRES RESEARCH) via Ollama/sentence-transformers.
- **Reranker** is a lexical-overlap stand-in; a cross-encoder is future (REQUIRES RESEARCH).
- **Streaming** replays the computed answer token-by-token; true per-token model streaming
  (Ollama/vLLM) is a later increment.
- **Live OpenSearch + real Ollama model** not exercised here (environment/network).
- Response cache and token budgets are in-process; a shared (Redis) store is future.
- No trained **Dula AI** model yet (Phase 04); this MVP uses a general model.

## Lessons learned
- Designing every AI component offline-first (hashing embedder, in-memory stores, extractive
  provider) made the whole pipeline CI-testable and genuinely air-gapped, with real backends as
  drop-in config — directly satisfying the deploy-anywhere principle.
- A relevance floor (content-token overlap, stopword-filtered) is needed so an always-returns-k
  retriever does not ground out-of-domain questions (a real hallucination-guard bug caught by the
  benchmark test).
- Hyphenated package dirs force test files to top-level module names; duplicate basenames need
  pytest `--import-mode=importlib` and tests excluded from the mypy source gate.

## Next milestone / gaps / status
- **Next milestone:** M004 — Phase 04 (Dula AI): datasets, training/eval pipelines, model serving.
- **Documentation gaps:** model/training docs pending Phase 04.
- **Final status:** **COMPLETE** (required technical + user documentation present and verified;
  acceptance criteria met — grounded cited answers above baseline, injection basics pass, works
  fully offline).
