---
title: Project State (Current Execution State)
document_id: STATE-000
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Engineering leadership
audience: All contributors (and future context recovery)
phase: Documentation Bootstrap (M000)
---

# PROJECT_STATE

> **Purpose.** Current, frequently-changing execution state. Update this on every
> meaningful change. For durable knowledge, see [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md).

## Current Snapshot

| Field | Value |
|-------|-------|
| **CURRENT PHASE** | Phase 05 — Cyber Intelligence (COMPLETE) |
| **CURRENT MILESTONE** | M005 ✅ complete |
| **STATUS** | Phase 05 done & **closed under CLAUDE.md §11** (M005 Closure + Phase 05 Completion Review). Delivered on `main`: a **deterministic, offline-first intelligence core** (`dula_ai.intel`) — CTI extraction (IOC/TTP + STIX 2.1), CVSS v3.1 scoring + P1–P4 prioritization, and Sigma/YARA authoring with validators + ATT&CK coverage — exposed via `apps/ai-gateway` `/api/v1/intel/*` (OPA `ai.cti`/`ai.vuln`/`ai.detect`), gated by domain benchmark + red-team suites. Ruff/format/mypy clean; **129 pytest**. |
| **LAST COMPLETED TASK** | Phase 05 build + closure: [M005 Closure](./04-MVP-Roadmap/closure/M005-CyberIntelligence-Closure.md) + [Phase 05 Completion Review](./04-MVP-Roadmap/closure/Phase05-CyberIntelligence-Completion-Review.md) |
| **CURRENT TASK** | — (Phase 05 complete; awaiting go-ahead for Phase 06) |
| **NEXT TASK** | Phase 06 — Agents (LangGraph, ADR-0008; NOT started; do not begin without direction). Dula AI iterations (larger base) continue on the Phase 04 pipeline, shipping only if they clear the gate. |
| **BLOCKERS** | None. Connections live: HF (AmanuelFeyissa), Modal, Kaggle. Repo: github.com/AmanuelFeyissa/dula (private) |

## What Exists

- `docs/` — full engineering handbook (reviewed in M000); `docs/adr/` — ADR-0001…0011 (Accepted).
- **Monorepo `dula`** on private GitHub with CI (docs/python/web/security gates green).
- `packages/common-py` (config, JSON logging, OIDC verifier, OPA client, event publisher);
  **`packages/dula-ai`** (LLM Gateway + RAG: chunking, embeddings, Qdrant/OpenSearch stores,
  hybrid retrieval, guardrails, providers, knowledge ingestion, offline factory + benchmark;
  **`dula_ai.intel`**: deterministic CTI/vuln/detection engineering — see below);
  `apps/platform-api` (CRUD for assets/incidents/alerts, OPA authz, audit, RLS);
  `apps/worker` (idempotent Redpanda consumer); **`apps/ai-gateway`** (grounded Q&A, triage,
  knowledge ingest, **cyber-intelligence `/intel/*`**; SSE streaming); `apps/web` (app shell +
  alerts/incidents/assets + **Ask/triage UI** + **Intel workbench UI**); Keycloak realm; OPA
  `dula.authz` policy; Docker Compose dev stack (Qdrant, OpenSearch, Redpanda, OPA, Postgres,
  Redis, MinIO, optional Ollama).
- Grounded Q&A/triage run on a **general model** (offline extractive default; Ollama optional).
- **Phase 04 pipeline:** `packages/dula-ml` (torch-free logic) + `ml/` (standalone GPU project:
  QLoRA train, eval, decide; Kaggle/Lightning/Modal runners; DVC + Argo) + OpenAI-compatible
  serving provider. Datasets: **Primus** (ODC-BY/MIT); base **Qwen2.5/Mistral** (ADR-0007);
  compute on free GPU + HF Hub (ADR-0012). No trained Dula AI checkpoint exists yet.
- **Phase 05 cyber intelligence:** `dula_ai.intel` — deterministic, offline-first IOC/ATT&CK
  extraction with STIX 2.1 mapping (UC-05), CVSS v3.1 scoring + explainable P1–P4
  prioritization (UC-07), and Sigma/YARA authoring with always-validated output + ATT&CK
  coverage mapping (UC-04). A grounded CTI summary layers the LLM Gateway on top. Domain
  benchmark (extraction precision/recall, 100% rule validity) and red-team/dual-use safety
  suites gate it in CI.

## What Is Next

**Phase 05 (M005) is complete and closed under §11.** Phase 06 — Agents (LangGraph, ADR-0008)
is next, on explicit go-ahead. Dula AI iterations (a larger base model) continue on the Phase
04 pipeline, shipping only if a future candidate clears the evaluation gate. Remaining
non-blocking open items: API gateway tech, plugin sandbox mechanism, embedding/reranker model,
hardware sizing.

## Milestone Ledger

| Milestone | Phase | Status |
|-----------|-------|--------|
| M000 | Documentation Bootstrap | ✅ Docs complete + reviewed; ADR-0001…0011 Accepted |
| M001 | Phase 01 — Foundation | ✅ Complete (PR #1 merged; live OIDC verified) |
| M002 | Phase 02 — Core Platform | ✅ Complete (domain spine + events + OPA + UI; isolation/OPA/events verified live) |
| M003 | Phase 03 — Knowledge & RAG | ✅ Complete (LLM Gateway + RAG + AI Gateway + Ask UI; benchmark + red-team; Qdrant verified live) |
| M004 | Phase 04 — Dula AI | ✅ Complete (pipeline + real QLoRA run; first candidate **retired** by the gate; platform stays on general model) |
| M005 | Phase 05 — Cyber Intelligence | ✅ Complete (CTI extraction + STIX, CVSS/prioritization, Sigma/YARA authoring + validation, ATT&CK coverage; intel API; benchmark + red-team gates) |
| M006+ | Phases 06–11 | ⏳ Not started |

## Open Items Requiring Human Action

- Sign off the reviewed foundation and ADR-0001…0010.
- Decide remaining open items (API gateway, sandbox mechanism, monorepo confirmation).
- Verify **REQUIRES RESEARCH** items before they inform implementation
  (see [PROJECT_CONTEXT.md](./PROJECT_CONTEXT.md) §8 and
  [PROJECT_REVIEW-M000.md](./PROJECT_REVIEW-M000.md) §9).
- Accept the residual risks or adjust scope (resourcing, air-gapped GPU/UX — review §12).

## Change Log

- 2026-08-11 — M000 documentation foundation created (AI-assisted, Draft).
- 2026-08-11 — Product naming decided: **Dula** / **Dula AI** (ADR-0001); all docs renamed.
- 2026-08-11 — M000 architecture & documentation review completed
  ([PROJECT_REVIEW-M000.md](./PROJECT_REVIEW-M000.md)); ADR-0001…0010 Accepted; contradictions
  (vector DB, event bus, agent runtime), MVP over-scope, and cross-tenant AI isolation
  resolved in the affected docs.
- 2026-08-11 — **Decisions promoted from MVP-staging to permanent, production-grade.**
  ADR-0002/0003/0004 revised: vector store = **Qdrant**, search/log-analytics =
  **OpenSearch**, event backbone = **Redpanda (Kafka API)**, **Go** approved for the
  data-plane. All "for MVP / on trigger / migrate later" staging removed across the docs;
  the chosen stack is now the permanent target (changeable only via a superseding ADR if a
  materially better technology emerges).
- 2026-08-12 — **Phase 01 (M001) build.** Monorepo initialized (ADR-0011) and pushed to
  private GitHub repo `AmanuelFeyissa/dula`. Delivered: root tooling (uv/ruff/mypy strict,
  pnpm/tsc), Docker Compose dev stack, CI gates; `packages/common-py` (config, JSON logging,
  OIDC verifier); `apps/platform-api` (FastAPI healthz/readyz + `/api/v1/me`, DB, Alembic
  initial migration with RLS); Keycloak `dula` realm export; OPA authz policy (+tests);
  `apps/web` Next.js login shell (Keycloak OIDC). Verified: ruff clean, mypy strict clean
  (19 files), 8 pytest pass, web builds, migration applied+rolled back on live Postgres.
- 2026-08-12 — **Phase 01 (M001) complete.** PR #1 merged to `main`; CI green
  (docs/python/web/security). Live end-to-end OIDC verified: Keycloak issued `maya` a token
  (aud `dula-api`, tenant_id, role `analyst`) and `GET /api/v1/me` returned HTTP 200 with the
  verified claims. Fixed a `/readyz` status-label bug (reported `degraded` while DB was ok)
  and added regression tests (10 pytest total).
- 2026-08-12 — **Documentation lifecycle governance added.** New **CLAUDE.md §11 (Phase &
  Milestone Documentation Closure)** makes technical + user/operator documentation part of
  the Definition of Done (impact assessment, checklist, Milestone Closure Report / Phase
  Completion Review, `DOCUMENTATION-INCOMPLETE` status). Added `docs/17-User-Documentation/`
  and `docs/04-MVP-Roadmap/closure/` (with a retroactive M001 closure report). Referenced
  from DocumentationStandards §11, MVPOverview §5 DoD, NamingConventions (USR prefix),
  Glossary, and SUMMARY. No ADRs changed.
- 2026-08-12 — **Phase 01 closed under §11.** Added the Phase 01 Completion Review; ran the
  §11.9 phase verification (links, terminology, architecture/security consistency). Phase 01
  now satisfies the strengthened DoD: implementation + tests + security + technical/user
  documentation + M001 Closure + Phase Completion Review. Ready for Phase 02 on go-ahead.
- 2026-08-12 — **Phase 02 (M002) build + closure.** Delivered the core domain: `assets`,
  `incidents`, `alerts` (+ immutable `audit_events`) via migration `0002_domain_spine` with
  RLS on every tenant table; tenant-scoped repositories + application services (ports &
  adapters); 15 CRUD endpoints ([12-API/CoreDomainAPI.md](./12-API/CoreDomainAPI.md)) with
  service-layer OPA authorization (fail-closed, audited) and domain-event emission; the shared
  `EventPublisher` + `apps/worker` idempotent Redpanda consumer; OPA added to the dev stack;
  and a Next.js app shell with alerts/incidents/assets list/detail views over a typed API
  client. Verified: ruff/format/mypy-strict clean, **26 pytest**, **OPA 11/11**, web build;
  live Alembic upgrade/downgrade roundtrip, RLS/policies present, live OPA decisions, and a
  full event round-trip with idempotent dedupe. Closed under §11 (M002 Closure + Phase 02
  Completion Review). Deferred: K8s deploy, RLS FORCE + non-owner role, UI write forms, E2E in
  CI. Ready for Phase 03 on go-ahead.
- 2026-08-12 — **Phase 03 (M003) build + closure.** Delivered the first shippable MVP: the
  model-agnostic **LLM Gateway** (`packages/dula-ai`) with pluggable providers (offline
  `extractive-v1` default; Ollama), per-tenant token budgets, per-tenant response cache, output
  secret-redaction, and audit; the **RAG** subsystem (chunking, hashing/Ollama embeddings,
  Qdrant + OpenSearch stores, RRF hybrid retrieval with tenant filtering + reranking, guardrails,
  cited context) with knowledge ingestion (license checks + purge); **`apps/ai-gateway`**
  (grounded Q&A `/ask` + SSE `/ask/stream`, `/triage`, `/knowledge`); expanded OPA policy; optional
  Ollama in the dev stack; and an **Ask/triage UI** with streaming + evidence. Added an offline RAG
  **evaluation benchmark** (recall/citation/groundedness baselines) and **AI red-team** injection
  tests. Verified: ruff/format/mypy-strict clean, **56 pytest**, **OPA 16/16**, web build; **live
  Qdrant** ingest/retrieve with tenant payload filtering. Closed under §11 (M003 Closure + Phase 03
  Completion Review). Deferred: live OpenSearch verify (image pull blocked on constrained network;
  adapter code-complete + BM25 unit-tested), real Ollama model call, semantic embeddings, K8s
  deploy. Ready for Phase 04 on go-ahead.
- 2026-08-12 — **Phase 04 (M004) complete — first candidate retired.** Connected HF/Modal/Kaggle;
  chose MMLU `computer_security` (MIT) as the permissive benchmark; hardened the trainer (trl arg
  rename, fp16-on-T4 vs bf16, adapter merge, ShareGPT mapping) — caught cheaply by a Modal CPU
  validation. Ran a **real QLoRA fine-tune** (Qwen2.5-0.5B on Primus-Instruct, ODC-BY/MIT) on
  free-credit Modal and evaluated candidate vs the general-model baseline: **accuracy 0.360 vs
  0.370, safety-refusal 0.250 vs 0.500 → gate = RETIRE.** Correct outcome (never ship a worse/
  less-safe model); nothing pushed; platform continues on the general model + RAG. Decision
  recorded in `ml/registry/` (model card + manifest). Closed under §11 (M004 Closure + Phase 04
  Completion Review). Verified: ruff/format/mypy clean, 81 pytest.
- 2026-08-12 — **Phase 04 (M004) pipeline delivered.** Built the Dula AI train→eval→**gate**→
  register→serve pipeline: torch-free, CI-tested `packages/dula-ml` (SFT record formatting,
  dedup, benchmark contamination check, training-data safety filter, MCQ/safety scoring, the
  **ship/retire gate**, registry manifest + model card) and the standalone `ml/` GPU project
  (`dula_train`: data_prep/train_qlora/eval_runner/decide; Kaggle/Lightning/Modal runners; MLflow;
  `dvc.yaml`; Argo workflow). Added an **OpenAI-compatible serving provider** to the gateway so a
  shipped checkpoint plugs in with no app change, and **ADR-0012** (free GPU training + HF Hub +
  keep GitHub; Primus datasets; Qwen/Mistral base). Verified: ruff/format/mypy-strict clean,
  **80 pytest**, web build; heavy training excluded from the workspace to keep CI light and the
  local disk clear. **Not yet COMPLETE:** the actual QLoRA run + recorded ship/retire decision
  execute on the user's free GPU accounts (no local GPU); M004 closes after that decision. Also
  did housekeeping: freed ~4.7 GB of Docker images (compaction needs an elevated diskpart run) and
  saved environment/platform decisions to memory.
- 2026-08-13 — **Phase 05 (M005) build + closure — Cyber Intelligence.** Delivered
  `dula_ai.intel`, a deterministic, offline-first intelligence core: IOC extraction (defang/
  refang-aware, 9 indicator kinds) + a curated ATT&CK technique catalog with keyword/ID
  extraction, mapped to a deterministic **STIX 2.1** bundle; **CVSS v3.1** base-score
  computation (spec-accurate Roundup) blended with contextual signals (KEV, exposure,
  criticality, patch status) into an explainable **P1–P4** priority; and **Sigma/YARA**
  authoring with dependency-free structural validators (every generated rule is checked before
  return) plus ATT&CK coverage-gap reporting. A grounded, non-speculative CTI summary layers
  the existing LLM Gateway on top (advisory treated as untrusted evidence). Exposed via six new
  `apps/ai-gateway` `/api/v1/intel/*` endpoints behind new OPA actions (`ai.cti`/`ai.vuln`/
  `ai.detect`), and a new **Intel workbench** page in `apps/web`. Added a domain benchmark
  (IOC/TTP precision-recall, 100% rule-validity) and red-team/dual-use safety tests (injected
  advisories don't leak the system prompt; secrets are redacted). Verified: ruff/format/mypy
  strict clean, **129 pytest** (up from 86), web lint/typecheck/build clean. Closed under §11
  (M005 Closure + Phase 05 Completion Review). Ready for Phase 06 on go-ahead.
