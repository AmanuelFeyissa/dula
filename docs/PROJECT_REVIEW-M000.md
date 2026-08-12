---
title: Architecture & Documentation Review — M000
document_id: REV-000
status: Reviewed
version: 1.0.0
last_updated: 2026-08-11
owner: Architecture
audience: Engineering leadership, architects
phase: Documentation Bootstrap (M000)
related:
  - ./PROJECT_STATE.md
  - ./adr/ADR-0001-product-naming.md
  - ./00-Governance/ArchitectureDecisionRecords.md
---

# Architecture & Documentation Review — M000

> **Purpose.** A complete review of the engineering foundation created in M000, covering
> governance, vision, architecture, technology, roadmap, Dula AI strategy, AI/security
> architecture, deployment, MLOps, testing, and project state. Findings are followed by
> the exact documents to revise and the ADR decisions taken. **No implementation was done.**

> **Update (2026-08-11, post-review):** the project owner directed that the architecture be
> treated as **permanent and production-grade**, not an MVP. The MVP-staging outcomes below
> were therefore **superseded**: finding **O1** (defer OpenSearch; pgvector + Postgres FTS
> for the MVP) no longer applies, and **ADR-0003/0004** were revised to their permanent form
> — **Qdrant** (vectors), **OpenSearch** (BM25/log-analytics), **Redpanda/Kafka** (event
> backbone) from the start, plus **Go** approved for the data-plane (ADR-0002). This report
> is retained as the historical record of the review; for current decisions see
> [adr/README.md](./adr/README.md) and [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md).

## 0. Overall Assessment

The foundation is coherent, internally cross-referenced, and honest about maturity. The
main issues are **(a) a few real contradictions from candidate-vs-recommendation drift**,
**(b) an over-scoped first MVP**, **(c) two genuinely under-specified security areas
(cross-tenant AI isolation; embedding/cache leakage)**, and **(d) resourcing realism** for
a two-product ecosystem. All are addressed below and by ADR-0001…0010.

Severity legend: 🔴 must-fix before implementation · 🟠 should-fix · 🟡 track/monitor.

## 1. Contradictions

| # | Sev | Finding | Resolution |
|---|-----|---------|-----------|
| C1 | 🔴 | **Vector DB**: `TechnologyStack.md` summary table lists *Qdrant* as "Recommended", but its own body, `RAGArchitecture.md`, and `PROJECT_CONTEXT.md` all say **start with pgvector**. | ADR-0003: **pgvector for MVP**, Qdrant on trigger. Fix the table. |
| C2 | 🟠 | **Event backbone**: table "Recommended NATS" while text implies Kafka may be needed; risk of implying *both* run by default. | ADR-0004: **NATS only** until a measured trigger; never both by default. |
| C3 | 🟠 | **Agent runtime**: `AgentArchitecture.md`/`TechnologyStack.md` lean "custom graph runtime", while text also says LangGraph "aligns well". Ambiguous. | ADR-0008: **build on LangGraph**, wrap with Dula permission/approval/audit. |
| C4 | 🟡 | **Backend language**: Go listed as candidate in several places; could be read as planned. | ADR-0002: **Python-only for MVP**; Go only if perf tests prove need. |
| C5 | 🟡 | **OWASP reference** in `AIThreatModel.md` said "verify current version". | Now pinned to **OWASP LLM Top 10 : 2025** with T-ID mapping. |

## 2. Missing Dependencies

- 🟠 **M1 — Cross-tenant AI isolation** is not specified for *shared model serving*: prompt
  caching / KV-cache reuse and a shared vector index can leak across tenants. (See §6/§7.)
- 🟠 **M2 — API gateway technology** is unspecified (Envoy vs custom FastAPI edge). Marked
  REQUIRES DECISION; not yet an ADR.
- 🟠 **M3 — Regulatory/compliance mapping** (e.g. for gov/regulated target users) is thin;
  `DataSecurity.md` covers mechanics but not a compliance framework mapping.
- 🟡 **M4 — Embedding-model versioning** in the registry (re-embedding is mentioned but the
  embedding model is not a first-class registry artifact).
- 🟡 **M5 — Cost/FinOps** guidance (GPU spend, token budgets) has no home doc.
- 🟡 **M6 — Feedback loop** from analyst corrections back into eval/datasets is not defined.

## 3. Unrealistic Assumptions

- 🟠 **U1 — Scope vs resourcing.** Building a full enterprise platform **and** a specialized
  LLM with scaled MLOps is very large; no team-size/timeline is stated. The phasing helps,
  but leadership must confirm resourcing or narrow scope. (Tracked as a risk.)
- 🟠 **U2 — Air-gapped GPU availability.** Many on-prem/air-gapped customers lack GPUs; the
  CPU/quantized fallback may be too slow for good UX on larger models. Requires explicit
  minimum-hardware tiers and honest UX expectations.
- 🟡 **U3 — Phase 04 acceptance ("Dula AI beats the general model").** Tuning a small model
  to beat a strong general model on broad security tasks is not guaranteed; RAG may
  dominate. The "ship only if better" gate is correct, but the *milestone* should not be a
  blocker — reframe Phase 04 acceptance to "either beats general model, or is retired with
  findings" (already close; make explicit).
- 🟡 **U4 — Expert-authored benchmark** assumes access to security experts for authoring and
  scoring; confirm this capacity.

## 4. Over-Engineering

- 🟠 **O1 — First MVP (Phase 03) is heavy.** It introduces LLM gateway + RAG + **OpenSearch
  hybrid search** + benchmark at once. Recommendation: **defer OpenSearch**; use
  **pgvector + PostgreSQL full-text search** for the MVP, add OpenSearch when log-analytics
  scale demands it. Reduces moving parts to reach the first usable MVP.
- 🟡 **O2 — Dual protocol (REST + gRPC)** from the start. Start **REST-only**; add gRPC only
  where a measured hot path needs it.
- 🟡 **O3 — Bespoke agent runtime** (addressed by ADR-0008: build on LangGraph).
- 🟡 **O4 — Running NATS *and* Kafka** (addressed by ADR-0004).

## 5. Under-Engineering

- 🔴 **N1 — Cross-tenant AI isolation** (see M1/§6/§7) — elevate to a first-class control.
- 🟠 **N2 — Embedding/vector weaknesses** (OWASP LLM08): embedding inversion / membership
  inference / cross-tenant retrieval need explicit controls beyond "namespacing".
- 🟠 **N3 — Compliance mapping** (M3).
- 🟡 **N4 — Unbounded consumption** (OWASP LLM10): quotas exist but token/cost budgets and
  per-tenant caps need concrete definition.

## 6. Security Risks

- 🔴 **S1 — Cross-tenant leakage via shared inference**: prompt/KV cache reuse and a shared
  vector index could expose one tenant's data to another. **Control:** never share
  prompt/KV cache across tenant boundaries; per-tenant embedding namespaces enforced at the
  gateway and RAG layers; test explicitly.
- 🟠 **S2 — Poisoned model weights** from open-weight downloads: verify provenance/hashes of
  base models (supply chain for models, not just code).
- 🟡 **S3 — Sensitive data in AI audit logs**: AI-call logging must redact prompts/outputs
  containing secrets/PII (partly covered; make explicit for the AI audit path).
- 🟢 Well-covered already: prompt injection→tool abuse, SSRF via connectors, secret
  management, sandboxing, supply chain for code.

## 7. AI / LLM Risks (mapped to OWASP LLM Top 10 : 2025)

| OWASP 2025 | Covered? | Notes |
|-----------|----------|-------|
| LLM01 Prompt Injection | ✅ | Direct + indirect; untrusted-content model |
| LLM02 Sensitive Info Disclosure | ✅ (+S3) | Add AI-audit redaction detail |
| LLM03 Supply Chain | ✅ (+S2) | Add model-weight provenance |
| LLM04 Data & Model Poisoning | ✅ | RAG + training poisoning covered |
| LLM05 Improper Output Handling | ✅ | Never exec model output; schema validation |
| LLM06 Excessive Agency | ✅ | Permissions + approval + limits |
| LLM07 System Prompt Leakage | 🟠 | **Add**: assume prompts leak; no secrets in prompts |
| LLM08 Vector & Embedding Weaknesses | 🟠 | **Add**: N2/S1 — cross-tenant, inversion |
| LLM09 Misinformation | ✅ | Grounding + citations + hallucination eval |
| LLM10 Unbounded Consumption | 🟠 | **Add**: token/cost caps (N4) |

## 8. Roadmap Problems

- 🟠 **R1 — MVP scope** (O1): trim Phase 03 to pgvector + Postgres FTS.
- 🟡 **R2 — Agents (P06) before Integrations (P07)**: agents are most useful with connectors.
  Acceptable (internal read-only tools first), but note the dependency and keep P06 scoped
  to internal tools only.
- 🟡 **R3 — Phase 04 milestone framing** (U3): make "retire if not better" explicit so the
  roadmap can't stall on model quality.
- 🟢 Phasing, dependencies, and DoD structure are otherwise sound.

## 9. Technology Decisions Requiring Research (status)

| Item | Status after this review |
|------|--------------------------|
| Base model family/license | **Resolved** ADR-0007 (prefer Apache-2.0: Qwen/Mistral; Llama deprioritized) |
| Vector DB threshold | **Resolved** ADR-0003 (pgvector→Qdrant) |
| Event backbone | **Resolved** ADR-0004 (NATS→Kafka on trigger) |
| Serving runtime | **Resolved** ADR-0005 (vLLM + llama.cpp) |
| Agent runtime | **Resolved** ADR-0008 (LangGraph-based) |
| Search at MVP (OpenSearch vs Postgres FTS) | **Resolved** (Postgres FTS at MVP; OpenSearch later) |
| Embedding/reranker model | Still **REQUIRES RESEARCH** (tune via retrieval eval) |
| API gateway tech | **REQUIRES DECISION** (M2) — narrow to Envoy vs FastAPI edge |
| Plugin sandbox mechanism | **REQUIRES DECISION** — default container isolation; spike WASM |
| Hardware sizing (train/infer) | **REQUIRES RESEARCH** (measure) |
| OpenSearch vs ClickHouse (log analytics) | **REQUIRES RESEARCH** (when analytics phase arrives) |
| SLSA target level | **REQUIRES RESEARCH** |

## 10. Documents To Revise (exact list)

| Doc | Change |
|-----|--------|
| [01-Project/TechnologyStack.md](./01-Project/TechnologyStack.md) | Fix vector-DB row (C1); crisp event-bus (C2); base-model note (ADR-0007); mark ADR rows Accepted; add API-gateway/search notes |
| [03-Architecture/RAGArchitecture.md](./03-Architecture/RAGArchitecture.md) | pgvector+Postgres FTS at MVP (O1); embedding-weakness controls (N2); cross-tenant namespacing (S1) |
| [03-Architecture/AIArchitecture.md](./03-Architecture/AIArchitecture.md) | Cross-tenant cache isolation (S1); LLM07 no-secrets-in-prompt |
| [03-Architecture/SystemArchitecture.md](./03-Architecture/SystemArchitecture.md) | Add cross-tenant AI isolation to multi-tenancy section (S1) |
| [03-Architecture/AgentArchitecture.md](./03-Architecture/AgentArchitecture.md) & [13-Agents/AgentFramework.md](./13-Agents/AgentFramework.md) | LangGraph-based (ADR-0008) |
| [10-Security/AIThreatModel.md](./10-Security/AIThreatModel.md) | Pin OWASP 2025 + map; add LLM07/LLM08/LLM10 controls; S1/S2/S3 |
| [08-AI/ModelSelection.md](./08-AI/ModelSelection.md) | Qwen/Mistral primary, Llama caveat (ADR-0007) |
| [04-MVP-Roadmap/Phase03-KnowledgeRAG.md](./04-MVP-Roadmap/Phase03-KnowledgeRAG.md) | Trim to pgvector+Postgres FTS (O1) |
| [04-MVP-Roadmap/Phase04-DulaAI.md](./04-MVP-Roadmap/Phase04-DulaAI.md) | "retire if not better" framing (R3) |
| [03-Architecture/ArchitectureRoadmap.md](./03-Architecture/ArchitectureRoadmap.md) | OpenSearch introduced later, not P03 |
| [00-Governance/ArchitectureDecisionRecords.md](./00-Governance/ArchitectureDecisionRecords.md) | Backlog → Accepted; link ADR files |
| [PROJECT_STATE.md](./PROJECT_STATE.md), [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md) | Reflect ADR decisions |
| New: [docs/adr/](./adr/ADR-0001-product-naming.md) | ADR-0001…0010 files |

## 11. ADR Decisions Taken (summary)

See [docs/adr/](./adr/ADR-0001-product-naming.md). All ten backlog ADRs are now **Accepted**;
three items remain intentionally open (API gateway, sandbox mechanism, and specific
embedding/reranker + hardware sizing which are empirical).

## 12. Residual Risks (watchlist → PROJECT_CONTEXT §7)

Resourcing (U1), air-gapped GPU/UX (U2), model-quality milestone (U3), cross-tenant AI
isolation verification (S1), compliance mapping (M3).
