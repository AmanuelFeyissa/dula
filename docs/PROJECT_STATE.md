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
| **CURRENT PHASE** | Phase 10 — MLOps at Scale (in progress; started on explicit go-ahead) |
| **CURRENT MILESTONE** | M011 🔄 in progress — MLOps at Scale (PR A merged: registry lifecycle stages) |
| **STATUS** | M010 done & **closed under CLAUDE.md §11** ([M010 Closure](./04-MVP-Roadmap/closure/M010-usability-durability-Closure.md)). A hands-on review of Phase 09's product found the backend solid but the UI read-only, unsearchable, showing approvers as raw UUIDs, storing agent/playbook runs only in memory, and bouncing visibly through Keycloak with no way to switch test personas short of recreating a container. Six PRs (A–F, `main` #17–#22) fixed all five: **A** Dula-themed Keycloak login (no interstitial) + real RP-Initiated Logout; **B** approvals attributed to real usernames + a token-leak fix; **C** filter/search/sort/pagination on alerts/incidents/assets (server-side severity ranking, URL-state-driven UI); **D** triage-edit and create Server Actions, role-aware and OPA-backed; **E** durable agent/playbook run persistence — **ADR-0016**, AI Gateway gains an *optional* Postgres dependency (`RUN_STORE=memory|postgres`, default memory), verified by tearing a FastAPI app down and confirming a run + its approval survive against a fresh instance; **F** replaced a stale, CI-unwired smoke spec with a 16-test per-persona E2E suite (analyst/responder/admin/second-tenant) plus a real axe accessibility sweep that found and fixed a missing `<main>` landmark, browser-default link-color contrast, and two chip color contrasts — all confirmed via re-running axe, not assumed fixed. 262 pytest passing; full E2E suite green 5 consecutive runs; doc-links/naming clean. |
| **LAST COMPLETED TASK** | M011 PR A: registry lifecycle stages (`dula_ml.lifecycle`, `ml/dula_train/promote.py`) |
| **CURRENT TASK** | M011 PR B — canary-aware serving + rollback wiring in the LLM Gateway |
| **NEXT TASK** | M011 PRs C–F: production monitoring/drift/auto-rollback, GPU serving-pool Helm + hardened Argo/DVC pipeline, a second real training candidate on a larger base model, then docs + M011/Phase 10 closure (see `docs/04-MVP-Roadmap/Phase10-MLOps.md`). Operational GA acceptance (live deploy, pen test, DR drill) from Phase 09 remains owned by the deploying team. |
| **BLOCKERS** | None. Connections live: HF (AmanuelFeyissa), Modal, Kaggle. Repo: github.com/AmanuelFeyissa/dula (private) |

## What Exists

- `docs/` — full engineering handbook (reviewed in M000); `docs/adr/` — ADR-0001…0016 (Accepted).
- **Monorepo `dula`** on private GitHub with CI (docs/python/web/security gates green).
- `packages/common-py` (config, JSON logging, OIDC verifier, OPA client, event publisher);
  **`packages/dula-ai`** (LLM Gateway + RAG: chunking, embeddings, Qdrant/OpenSearch stores,
  hybrid retrieval, guardrails, providers, knowledge ingestion, offline factory + benchmark;
  **`dula_ai.intel`**: deterministic CTI/vuln/detection engineering — see below);
  `apps/platform-api` (CRUD for assets/incidents/alerts + **filter/search/sort/pagination**, OPA
  authz, audit, RLS);
  `apps/worker` (idempotent Redpanda consumer); **`apps/ai-gateway`** (grounded Q&A, triage,
  knowledge ingest, **cyber-intelligence `/intel/*`**, **agents `/agents/*`**, **integrations
  `/plugins` + `/connectors/*`**; SSE streaming; **optional Postgres-backed agent/playbook run
  persistence, ADR-0016**); **`packages/dula-agents`** (agent runtime: tools, permissions,
  approval, limits, audit, planner, async `RunStore`); **`packages/dula-plugins`**
  (plugin/connector framework: Ed25519 signing, egress+SSRF, host lifecycle, connectors);
  **`packages/dula-automation`** (playbook framework: declarative steps + planner + grounded
  reporting + library);
  `apps/web` (app shell + alerts/incidents/assets with **filter/search/sort/pagination and
  triage-edit/create Server Actions** + **Ask/triage UI** + **Intel workbench** + **Agents** +
  **Integrations** + **Automation** UI; **Dula-themed Keycloak sign-in, no interstitial**; a
  **16-spec per-persona E2E suite** at `apps/web/e2e/`); Keycloak realm + Dula login theme; OPA
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
- **Phase 06 agents:** `dula_agents` — a first-party **agent runtime** (ADR-0008) that owns the
  security-critical layer: per-call permission checks (**agent ⊆ user**), human approval for
  consequential tools, step/cost/time limits, and a full audited, replayable run trace. The
  **investigation assistant** (UC-03) triages → enriches → corroborates → recommends a ticket
  (approval-gated) using read-first tools; the planner is deterministic/offline (LangGraph or a
  model planner can back it later behind the same interface). Exposed via `/api/v1/agents/*` and
  an `apps/web` Agents page. A **release-blocking safety suite** proves zero unauthorized actions
  under adversarial planners, missing permissions, rejected/unauthorized approvers, and runaway
  loops.
- **Phase 07 integrations:** `dula_plugins` — a **signed, sandboxed** plugin/connector framework:
  Ed25519 manifest signing with a trust store + revocation, a **default-deny egress allowlist with
  SSRF** protection, and a **host** that verifies-on-install, grants only manifest-declared
  permissions on enable, OPA-authorizes every capability call, bounds resources, and returns
  **untrusted** output. First connectors: `siem.search`, `ti.lookup_indicator` (+ egress-gated
  `ti.live_lookup`), `ticketing.create_ticket` (consequential). The investigation agent's
  `search_logs`/`create_ticket` tools are now **connector-backed** (agent→connector), the ticket
  still approval-gated. **Air-gapped-first**: egress is disabled by default so live-feed
  connectors are inert with no phone-home. Exposed via `/api/v1/plugins` + `/api/v1/connectors/*`
  and an `apps/web` Integrations page.
- **Phase 08 automation:** `dula_automation` — a **security automation** layer composing the agent
  runtime + connectors into **declarative, approval-gated playbooks** and **grounded reporting**. A
  playbook (`Ref`/`Template`/`Condition`/`PlaybookStep`) compiles into a stateless planner run by the
  *existing* `AgentRuntime`, so it adds **no new execution path** — allowlist ∩ user authz, human
  approval for consequential steps, limits, audit, and tenant isolation hold unchanged. Built-in
  `triage-enrich-ticket` playbook (read steps auto-run; ticket is an **approval checkpoint**);
  `generate_report` produces executive + technical reports grounded strictly in the trace (untrusted
  tool output; no unexecuted action claimed). Exposed via `/api/v1/automation/*` and an `apps/web`
  Automation page. High-volume telemetry ingestion is guarded by an offline throughput benchmark
  (`apps/worker`); cluster-scale load testing is documented as FUTURE.
- **Phase 09 production substrate:** `deploy/helm/dula` — one **umbrella Helm chart** deploying
  web/platform-api/ai-gateway/worker with hardened pods (non-root, read-only rootfs, dropped caps,
  seccomp, limits), probes, rolling updates, HPA, PDB, default-deny **NetworkPolicies**, **Gateway
  API** edge (ADR-0014), and a forward-only **pre-upgrade migration Job** — differentiated across
  **cloud/on-prem/hybrid/air-gapped** by values overlays only. Supply chain (ADR-0015):
  `deploy/kyverno` (verify cosign signatures + pod-security) + `.github/workflows/release.yml`
  (build→syft SBOM→grype gate→cosign keyed sign, gated on tag/dispatch). Air-gap: `deploy/airgap`
  (bundle manifest + mirror script + `verify-airgap.sh` no-egress assertion, passing in CI).
  Observability (`deploy/observability`: SLOs + Prometheus rules + Grafana dashboard) and backup/DR
  (`deploy/backup`: pg backup/restore). A CI **`deploy`** job validates the whole surface. **GA
  acceptance** (live deploy across profiles, external pen test, DR drill) is operational — tracked
  in `docs/11-Deployment/GAReadiness.md`.

## What Is Next

**Phase 09 (M009) is complete for its buildable scope and closed under §11**; the API-gateway and
supply-chain/admission open items are now **DECIDED (ADR-0014, ADR-0015)**. **Phase 10 — MLOps at
scale** (Argo Workflows/MLflow/DVC + GPU serving pools on the new deployment substrate) is next, on
explicit go-ahead. **Operational GA acceptance** — live deploy across all four profiles, external
penetration test, and a DR restore drill meeting RPO/RTO — is owned by the deploying team and needs
real infrastructure (GAReadiness.md). Dula AI iterations (a larger base model) continue on the Phase
04 pipeline, shipping only if a future candidate clears the evaluation gate. Remaining non-blocking
items: embedding/reranker model + hardware sizing (empirical); the app `/metrics` exporter; Terraform
IaC + GitOps (Argo CD); OS-level sandbox runners + real connector HTTP clients + third-party plugin
loader; and automation follow-ons (scheduled/triggered playbooks, durable run store, PDF reports,
cluster-scale telemetry load test).

## Milestone Ledger

| Milestone | Phase | Status |
|-----------|-------|--------|
| M000 | Documentation Bootstrap | ✅ Docs complete + reviewed; ADR-0001…0011 Accepted |
| M001 | Phase 01 — Foundation | ✅ Complete (PR #1 merged; live OIDC verified) |
| M002 | Phase 02 — Core Platform | ✅ Complete (domain spine + events + OPA + UI; isolation/OPA/events verified live) |
| M003 | Phase 03 — Knowledge & RAG | ✅ Complete (LLM Gateway + RAG + AI Gateway + Ask UI; benchmark + red-team; Qdrant verified live) |
| M004 | Phase 04 — Dula AI | ✅ Complete (pipeline + real QLoRA run; first candidate **retired** by the gate; platform stays on general model) |
| M005 | Phase 05 — Cyber Intelligence | ✅ Complete (CTI extraction + STIX, CVSS/prioritization, Sigma/YARA authoring + validation, ATT&CK coverage; intel API; benchmark + red-team gates) |
| M006 | Phase 06 — Agents | ✅ Complete (first-party agent runtime; investigation assistant UC-03; permissions/approval/limits/audit; agents API + UI; release-blocking safety suite) |
| M007 | Phase 07 — Integrations | ✅ Complete (signed plugin/connector framework; egress allowlist + SSRF; host lifecycle; SIEM/TI/ticketing connectors; plugins API + UI; agent→connector bridge; air-gapped verified) |
| M008 | Phase 08 — Automation | ✅ Complete (declarative approval-gated playbooks over the agent runtime; grounded reporting; automation API + UI; ingestion throughput benchmark; no-bypass/no-auto-approval safety) |
| M009 | Phase 09 — Production | ✅ Complete, buildable scope (Helm chart + 4 profile overlays; hardened workloads + Gateway API edge; Kyverno admission + cosign/SBOM release pipeline; air-gap tooling + no-egress assertion; observability + backup/DR; CI deploy job). **GA sign-off operational** (live deploy/pen-test/DR-drill pending real infra). ADR-0014/0015. |
| M010 | Usability & Durability Hardening | ✅ Complete (Dula-themed sign-in + real logout; usernames not UUIDs; filter/search/sort/pagination; triage-edit + create; durable agent/playbook runs — ADR-0016; per-persona E2E + real a11y fixes). Closed under §11: [M010 Closure](./04-MVP-Roadmap/closure/M010-usability-durability-Closure.md). |
| M011 | Phase 10 — MLOps at Scale | 🔄 In progress (started on explicit go-ahead). PR A merged: registry lifecycle stages. |
| M012+ | Phase 11 | ⏳ Not started |

## Open Items Requiring Human Action

- Sign off the reviewed foundation and ADR-0001…0010.
- Decide remaining open items (API gateway technology; monorepo confirmed as ADR-0011; plugin
  sandbox decided as ADR-0013).
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
- 2026-08-13 — **Phase 06 (M006) build + closure — Agents.** Delivered `packages/dula-agents`,
  a first-party **agent runtime** per ADR-0008: a plan/act loop where the planner only *proposes*
  and the runtime is the sole executor, running a step only after it passes the agent's tool
  **allowlist**, the invoking user's **OPA authorization** (agent ⊆ user), and — for consequential
  tools — **human approval**; with step/cost/time **limits** and a full **audited** run trace
  (lifecycle: planning→awaiting_approval→executing→completed/failed/halted). Built the **investigation
  assistant** (UC-03: list_alerts→enrich_indicator→search_logs→create_ticket, least-privilege — no
  host isolation), a deterministic offline planner (LangGraph/model planner can back the same
  interface later), tenant-scoped run store, and injectable tool **ports** (in-memory offline;
  real connectors FUTURE). `enrich_indicator` reuses the Phase 05 intel core. Exposed six OPA
  actions (`agents.run/read/approve` + `tool.*`) and `/api/v1/agents/*` (start/read/approve),
  plus an `apps/web` **Agents** page (run + approve/reject). Added a **release-blocking safety
  suite** asserting **zero unauthorized actions** under adversarial planners, missing permissions,
  rejected/unauthorized approvers, and runaway loops. Verified: ruff/format/mypy-strict clean,
  **157 pytest** (up from 129; +18 runtime +10 API), OPA policy extended, web eslint/tsc/build
  clean. Closed under §11 (M006 Closure + Phase 06 Completion Review). Ready for Phase 07 on
  go-ahead.
- 2026-08-13 — **Phase 07 (M007) build + closure — Integrations.** Delivered `packages/dula-plugins`,
  a **signed, sandboxed** plugin/connector framework (docs/14-Plugins): **Ed25519** manifest
  signing with a trust store + **revocation** (verify-on-install, tamper/untrusted-key rejected);
  a **default-deny egress allowlist with SSRF** protection (private/loopback/unresolvable blocked;
  globally disabled when air-gapped); a **host** with the full lifecycle (install→enable→disable→
  revoke) that OPA-authorizes every capability call, applies timeouts/output limits, and returns
  **untrusted** output; a connector **SDK**; and the first connectors — `siem.search`,
  `ti.lookup_indicator` + egress-gated `ti.live_lookup`, and consequential `ticketing.create_ticket`.
  Wired into `apps/ai-gateway` as `/api/v1/plugins` (list; `plugins.read`), enable/disable
  (`plugins.admin`), and `/api/v1/connectors/{cap}/invoke` (`connectors.invoke` + per-`connector.*`;
  consequential caps blocked from direct invoke → must go via an agent). **Bridged the investigation
  agent's `search_logs` + `create_ticket` tools to the SIEM/ticketing connectors** (agent→connector;
  ticket still approval-gated). Added an `apps/web` **Integrations** page. Verified: ruff/format/
  mypy-strict clean (**103 files**), **199 pytest** (up from 157; +31 package, +11 API), OPA policy
  extended, web eslint/tsc/build clean; **air-gapped inertness** of egress-gated connectors proven.
  Closed under §11 (M007 Closure + Phase 07 Completion Review). Ready for Phase 08 on go-ahead.
- 2026-08-13 — **Plugin sandbox mechanism DECIDED (ADR-0013).** Resolved the last Phase 07 open
  item: a **layered model behind a pluggable sandbox-runner** — an **out-of-process worker with
  host-brokered capabilities** (the plugin has **no ambient network**; all egress goes through the
  host's guard, so even a compromised plugin cannot open a socket) as the portable,
  air-gapped-capable baseline, hardened per platform (Linux: seccomp/namespaces/cgroups), and
  reinforced by a **rootless container** (gVisor/Kata) in orchestrated profiles; **WASM** is a
  future runner option (kept off the primary path while the SDK is Python-first). Realized in
  `packages/dula-plugins/sandbox.py` (`SandboxSpec` + `SandboxRunner` + default `InProcessRunner`,
  wired into the host); the OS-level worker/container runners are FUTURE. Updated ADR index/table,
  PluginArchitecture/Framework/Security + 10-Security/PluginSecurity, TechnologyStack, and CLAUDE.md
  §6 open items. Verified: ruff/format/mypy clean, **205 pytest** (+6 sandbox).
- 2026-08-13 — **Phase 08 (M008) build + closure — Automation.** Delivered `packages/dula-automation`,
  a security **automation** layer composing the agent runtime + connectors into **declarative,
  approval-gated playbooks** and **grounded reporting**. A playbook (`Ref`/`Template`/`Condition`/
  `PlaybookStep`/`Playbook`) compiles into a **stateless** `PlaybookPlanner` executed by the *existing*
  `AgentRuntime`, so it adds **no new execution path and no new security surface** — the runtime stays
  the sole executor and every control (allowlist ∩ user authz, human approval for consequential steps,
  limits, audit, tenant isolation) holds unchanged. Built-in `triage-enrich-ticket` playbook (read
  steps auto-run; `create_ticket` is an **approval checkpoint**); `generate_report` emits executive +
  technical reports grounded strictly in the trace (tool output labelled untrusted; no unexecuted
  action claimed). Wired into `apps/ai-gateway` as `/api/v1/automation/*` (list/run/read/approve/report)
  behind new OPA actions (`automation.read`/`run`/`approve`, `reports.read`); added an `apps/web`
  **Automation** page. Added an **offline high-volume ingestion throughput benchmark** (`apps/worker`,
  ADR-0004) — correctness + idempotency at volume + a per-event cost floor; cluster-scale load test
  documented as FUTURE. Verified: ruff/format/mypy-strict clean, **227 pytest** (up from 205; +12
  package, +8 API, +2 throughput), OPA policy extended, web eslint/tsc/build clean. Closed under §11
  (M008 Closure + Phase 08 Completion Review). Ready for Phase 09 on go-ahead.
- 2026-08-13 — **Phase 09 (M009) build + closure — Production.** Delivered the production substrate:
  an **umbrella Helm chart** (`deploy/helm/dula`) deploying all four services with hardened pods
  (non-root, read-only rootfs, dropped caps, seccomp, resource limits), probes, rolling updates
  (`maxUnavailable: 0`), HPA, PDB, default-deny **NetworkPolicies**, **Gateway API** edge, and a
  forward-only **pre-upgrade migration Job** — one chart, four **profile overlays**
  (cloud/on-prem/hybrid/air-gapped). Fixed the `ai-gateway` Dockerfile (missing workspace deps) and
  added a hardened **web** image. Supply chain: **Kyverno** admission (`deploy/kyverno`: verify
  cosign signatures + pod-security) and a gated **release pipeline** (`.github/workflows/release.yml`:
  build→syft SBOM→grype gate→cosign keyed sign). **Air-gap**: `deploy/airgap` bundle tooling +
  `verify-airgap.sh` no-egress assertion (passing in CI). **Observability** (`deploy/observability`:
  SLOs + Prometheus rules + Grafana dashboard) and **backup/DR** (`deploy/backup`). New CI **`deploy`**
  job (helm lint + template ×4 + kubeconform + air-gap assertion + policy/JSON validation). Resolved
  two long-open decisions I owned: **ADR-0014** (Envoy Gateway/Gateway API edge) and **ADR-0015**
  (cosign keyed signing + syft SBOM + grype + Kyverno; SLSA Build L3; signed-commit policy). Verified:
  helm lint clean, 26 manifests render per profile, kubeconform 19 valid/0 invalid, air-gap assertion
  passes; ruff/format/mypy clean, **227 pytest**, web build clean, doc-links/naming clean. Closed under
  §11 (M009 Closure + Phase 09 Completion Review). **GA sign-off is pending operational acceptance**
  (live multi-profile deploy, external pen test, DR drill with RPO/RTO — real infra required;
  GAReadiness.md). A live Postgres **backup/restore roundtrip was executed and verified** (backup →
  drop → checksum-verified restore → all rows recovered, real pg_dump/pg_restore). Added a top-level
  **RUNNING.md** run-the-system guide (URLs + dev credentials), and the local dev stack was brought
  up end-to-end (web + platform-api + ai-gateway + Keycloak/OPA/Postgres, offline profile). Ready
  for Phase 10 on go-ahead.
- 2026-08-18 — **Phase 09/M009 GA sign-off item deferred; M010 (Usability & Durability
  Hardening) built and closed under §11** (six PRs, `main` #17–#23; see the M010 row above and
  [M010 Closure](./04-MVP-Roadmap/closure/M010-usability-durability-Closure.md) for the full
  account). **Phase 10/M011 (MLOps at Scale) started on explicit go-ahead.** PR A delivered the
  model registry lifecycle state machine: `RegistryEntry.stage` (docs/09-MLOps/ModelLifecycle.md's
  Register→Staging→Canary→Production→Superseded/Rejected/Archived edges) and
  `dula_ml.lifecycle.promote()`, which appends transition entries to the existing append-only
  JSONL manifest, auto-supersedes the prior production version, and treats rollback as simply
  re-promoting a superseded version back to production — exposed via a small CLI
  (`ml/dula_train/promote.py`). A code-review pass before merging caught and fixed a real bug
  (`latest_shipped()` no longer distinguished original ship/retire registrations from later
  lifecycle transitions carrying the same `decision`) and a concurrency gap (two near-simultaneous
  promotions to `production` could both succeed); both fixed with tests. Verified: ruff/format/
  mypy clean, full workspace pytest green (30/30 in `packages/dula-ml`).
