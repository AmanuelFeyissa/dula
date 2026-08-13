---
title: Milestone Closure — M005 (Phase 05 Cyber Intelligence) — Complete
document_id: MVP-M005-CLOSURE
status: Reviewed
version: 1.0.0
last_updated: 2026-08-13
owner: Engineering
audience: Project Maintainer, Developer, Architect, Security Engineer, ML Engineer, DevOps/SRE
phase: Phase 05 — Cyber Intelligence (M005)
related:
  - ../Phase05-CyberIntelligence.md
  - ../../08-AI/CyberIntelligence.md
  - ../../12-API/AIGatewayAPI.md
  - ../../17-User-Documentation/CyberIntelligenceUserGuide.md
  - ../../PROJECT_STATE.md
  - ./README.md
---

# Milestone Closure — M005 (Phase 05 Cyber Intelligence)

> Produced per **CLAUDE.md §11.8**. **This milestone is COMPLETE.** CTI extraction (UC-05),
> vulnerability analysis (UC-07), and detection authoring (UC-04) are delivered as a
> deterministic, offline-first intelligence core with grounded/validated outputs, exposed
> through `apps/ai-gateway`, gated by domain benchmark suites, and closed with technical + user
> documentation.

- **Milestone identifier:** M005
- **Milestone name:** Phase 05 — Cyber Intelligence
- **Objective:** Deliver UC-05 (CTI extraction/summarization), UC-07 (vulnerability analysis),
  and UC-04 (Sigma/YARA authoring assist) with grounded, cited outputs and structured
  extraction. See [../Phase05-CyberIntelligence.md](../Phase05-CyberIntelligence.md).

## Implemented functionality
- **CTI extraction** — `dula_ai.intel.iocs` (IOC extraction with refang/defang and overlap
  resolution), `intel.attack` (ATT&CK technique extraction over a curated embedded catalog),
  `intel.stix` (deterministic STIX 2.1 bundle mapping), `intel.cti` (`CTIService`: structured
  extraction + optional grounded, guardrailed summary via the LLM Gateway).
- **Vulnerability analysis** — `intel.vuln`: faithful CVSS v3.1 base-score computation +
  qualitative severity, and a transparent P1–P4 prioritization blending severity with
  known-exploited / internet-exposure / asset-criticality / patch-availability signals, with a
  full rationale.
- **Detection authoring** — `intel.detections.sigma` and `...yara`: deterministic authoring
  from indicators with dependency-free emitters and **validators** (structural + external-text),
  and `...coverage` (ATT&CK coverage/gaps vs a target set). All authored rules are validated
  before return.
- **API** — `apps/ai-gateway` router `/api/v1/intel/*` (`extract`, `vulnerability`,
  `detections/sigma|yara|validate|coverage`) with per-action OPA authorization.
- **UI** — `apps/web` **Intel workbench** (`/intel`, nav-linked): CTI Extract / Vulnerability /
  Detections tabs over four server-side proxy routes (`/api/intel/*`) that inject the caller's
  token, mirroring the existing Ask/Triage proxy pattern.
- **Evaluation** — `intel.benchmark` + CI suites (extraction precision/recall, 100% rule
  validity, red-team/dual-use).

## Technical changes
- New subpackage `packages/dula-ai/src/dula_ai/intel/` (+ `detections/`), all torch-free and
  offline. New prompt version `cti-summary/v1` in `dula_ai.prompts` (advisory wrapped in the
  standard untrusted EVIDENCE envelope).
- New router `apps/ai-gateway/.../routers/intel.py`, registered in `main.py`.
- New `apps/web/app/intel/page.tsx` + `components/IntelWorkbench.tsx` + four `app/api/intel/*`
  proxy routes; `Nav.tsx` updated with an **Intel** link.

## Architecture changes
- None structural. Reuses the model-agnostic LLM Gateway (ADR-0005) and tenant/authorization
  model (ADR-0006/0009); the intelligence core is deterministic and adds no new infrastructure
  or product dependency (Sigma/YARA emitters are dependency-free — air-gapped guarantee
  preserved).

## Database changes
- None. The intel endpoints are stateless (the AI Gateway holds no database).

## API changes
- Added six `/api/v1/intel/*` endpoints (see
  [../../12-API/AIGatewayAPI.md](../../12-API/AIGatewayAPI.md)). New OPA actions `ai.cti`,
  `ai.vuln`, `ai.detect` (available to operational personas; tenant-scoped, fail-closed).

## Security changes / validation performed
- **Untrusted-source handling:** advisories/CVE records/draft rules treated as untrusted;
  indirect prompt injection is flagged and not obeyed; IOCs are **defanged on output**; the CTI
  summary passes the gateway's secret-redaction guard.
- **Dual-use safety:** detection authoring is deterministic and defensive-only (matching logic,
  not attack tooling); no offensive-generation path exists.
- **Red-team suite** (`test_intel_redteam.py`): injection-not-obeyed, secret-redaction,
  oversized-input rejection — all asserted in CI. OPA tests extended for the new actions
  (including cross-tenant denial).

## AI/ML changes
- Deterministic domain capabilities (no model training). Optional CTI summary uses the existing
  gateway/providers; a served Dula AI/Ollama model enriches summaries with no API change.

## Testing performed
- `ruff` + `ruff format --check` clean; `mypy --strict` clean (**76 source files**);
  **129 pytest pass, 5 skipped** (live-backend only), up from 108. New tests: intel IOC/ATT&CK/
  STIX/vuln/detections/CTI unit suites, the benchmark gate, the red-team suite, and 9
  ai-gateway endpoint integration tests. OPA policy extended (`opa test` in CI).
- `apps/web`: eslint clean, `tsc --noEmit` clean, `next build` succeeds with `/intel` and the
  four `/api/intel/*` routes registered.
- **Benchmark baselines asserted:** IOC precision ≥ 0.85, IOC recall ≥ 0.9, technique recall
  ≥ 0.9; 100% authored-rule validity.

## Deployment validation
- No new services or infrastructure; endpoints run in the existing `apps/ai-gateway` (offline
  profile verified via the test app). K8s/live-backend deployment unchanged from Phase 03.

## Documentation completed

### Documentation Impact Assessment (CLAUDE.md §11.6)
1. **Implemented:** CTI/vuln/detection capabilities + `/api/v1/intel/*` (above).
2. **Technical docs created:** [../../08-AI/CyberIntelligence.md](../../08-AI/CyberIntelligence.md); this closure; Phase 05 Completion Review.
3. **Technical docs updated:** AIGatewayAPI (intel endpoints), Benchmarking (§1b domain suites), SUMMARY, Glossary, PROJECT_STATE, PROJECT_CONTEXT, closure README.
4. **User docs created:** [../../17-User-Documentation/CyberIntelligenceUserGuide.md](../../17-User-Documentation/CyberIntelligenceUserGuide.md).
5. **User docs updated:** User-Documentation README index.
6. **Intentionally not created (N/A):** Database/Migration (no schema), Model card (no training), DR/Backup (stateless), Plugin/Agent (out of scope this phase).
7. **Examples/commands verified:** endpoint request/response shapes exercised by integration tests.
8. **Links valid:** relative-link check passes. 9. **Diagrams:** none required (no new architecture). 10-11. **Incomplete/gaps:** none blocking; curated catalog + behavioural-rule authoring are FUTURE, not M005 gaps.

### Milestone Documentation Checklist (CLAUDE.md §11.7)
#### Technical
- [x] Architecture updated (capability doc) · [x] API documentation updated · [N/A] Database
- [x] Configuration (OPA actions) · [x] Security documentation updated · [N/A] Deployment (no change)
- [x] Testing documentation updated · [~] Troubleshooting (user-guide "Good to know")
- [N/A] Operational/Runbook (stateless, no ops change) · [x] AI/ML updated · [N/A] RAG/Agent/Plugin
#### User
- [x] Getting Started / Feature docs (Cyber Intelligence User Guide) · [x] User guide updated
- [N/A] Admin/Operator guides (no operational surface) · [x] Troubleshooting notes · [N/A] FAQ
#### Quality
- [x] Front matter · [x] Naming conventions · [x] Relative links validated
- [x] Commands/examples verified · [x] No undocumented functionality · [x] No FUTURE-as-CURRENT
- [x] SUMMARY updated · [x] Glossary terms added · [x] PROJECT_CONTEXT/STATE updated

## Known limitations
- ATT&CK catalog and IOC/TTP heuristics are **curated**, not exhaustive; full-feed ingestion and
  semantic TTP mapping are FUTURE.
- Detection authoring covers **IOC-driven** rules; behavioural/complex-logic authoring is FUTURE.
- Offline CTI summary is extractive; richer narrative needs a served model behind the gateway.

## Known issues
- None outstanding.

## Deferred work
- Full ATT&CK/CVE feed ingestion into the knowledge base; STIX relationship objects; Sigma
  back-end conversion (e.g. to specific SIEM queries); YARA compilation against the real engine
  in CI; a larger labelled CTI benchmark (e.g. CTIBench).

## Lessons learned
- Making the intelligence core **deterministic** (not model-dependent) gave strong, testable
  guarantees — 100% rule validity and reproducible extraction — while keeping everything
  air-gapped and CI-light. The model is reserved for where judgement genuinely helps.

## Next milestone
- **Phase 06 — Agents** (LangGraph, ADR-0008) on explicit go-ahead. Not started.

## Documentation gaps
- None blocking. Curated-catalog expansion and behavioural-rule authoring will get their own
  docs when built.

## Final status
- **COMPLETE** — implementation + tests + security validation + technical *and* user
  documentation delivered and verified; benchmark gates green in CI.
