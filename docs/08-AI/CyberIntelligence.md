---
title: Cyber Intelligence (CTI, Vulnerability Analysis, Detection Authoring)
document_id: AI-015
status: Draft
version: 0.1.0
last_updated: 2026-08-13
owner: AI / Backend
audience: Developer, Security Engineer, ML Engineer
phase: Phase 05 — Cyber Intelligence (M005)
related:
  - ./RAGEngineering.md
  - ./Benchmarking.md
  - ../03-Architecture/AIArchitecture.md
  - ../12-API/AIGatewayAPI.md
  - ../10-Security/AIThreatModel.md
  - ../02-Vision/UseCases.md
  - ../17-User-Documentation/CyberIntelligenceUserGuide.md
---

# Cyber Intelligence

> **Purpose.** Technical reference for the Phase 05 domain capabilities delivered in
> **`packages/dula-ai/src/dula_ai/intel/`** and exposed by **`apps/ai-gateway`**: CTI
> extraction (UC-05), vulnerability analysis (UC-07), and detection authoring (UC-04).
> **Status: CURRENT** (offline profile). User guide:
> [../17-User-Documentation/CyberIntelligenceUserGuide.md](../17-User-Documentation/CyberIntelligenceUserGuide.md).

## Design stance

The intelligence core is **deterministic and offline-first**. IOC/TTP extraction, STIX
mapping, CVSS scoring, and Sigma/YARA authoring are **pure functions** — no model, no network
— so they run in air-gapped deployments and are exactly reproducible in CI. A model adds value
only where judgement helps (the optional CTI *summary*), and even then the structured
extraction remains authoritative. This keeps the consequential outputs — a priority decision, a
detection rule — **explainable and auditable**, never a black box.

Everything ingested is **untrusted** (advisories, CVE records, draft rules): the
AI threat model (OWASP LLM Top-10 2025, [../10-Security/AIThreatModel.md](../10-Security/AIThreatModel.md))
applies. IOCs are **defanged on output** so intel is never rendered as a live link, and
detection authoring is **defensive-only**.

## 1. CTI extraction (UC-05)

`dula_ai.intel.iocs`, `dula_ai.intel.attack`, `dula_ai.intel.stix`, `dula_ai.intel.cti`.

- **IOC extraction** (`iocs.extract`) — IPv4/IPv6, domains, URLs, emails, MD5/SHA-1/SHA-256,
  and CVE IDs. Defanged advisory text (`hxxp://`, `1[.]2[.]3[.]4`, `evil[.]com`,
  `user[at]corp[.]com`) is **refanged** before matching and **defanged** again on output.
  Overlaps are resolved so each substring is reported once at its most specific kind (a URL
  host is not also a bare domain; a 64-hex string is a SHA-256, not an MD5 substring).
- **ATT&CK TTP extraction** (`attack.extract_techniques`) — explicit technique IDs
  (`T1059.001`) plus keyword association against a curated, embedded ATT&CK catalog. Full
  ATT&CK ingestion is FUTURE via the knowledge pipeline.
- **STIX 2.1 mapping** (`stix.build_bundle`) — `indicator` SDOs (STIX patterning) and
  `attack-pattern` SDOs. IDs are `uuid5`-derived, so the same intel always produces the same
  bundle (idempotent, diffable) with no STIX library dependency.
- **Grounded summary** (`cti.CTIService`) — optional, via the LLM Gateway. The advisory is
  wrapped in the standard delimited EVIDENCE envelope (untrusted data, never instructions) and
  the summary passes the same output guardrails (secret redaction) as every AI call.

## 2. Vulnerability analysis (UC-07)

`dula_ai.intel.vuln`.

- **CVSS v3.1 base score** (`parse_cvss_vector`) — a faithful implementation of the official
  specification (metric weights, scope-aware impact, Roundup). Malformed or incomplete vectors
  raise `CvssError`.
- **Prioritization** (`prioritize`) — blends CVSS severity (up to 70 of a 0–100 risk score)
  with contextual signals: known-exploited (KEV), internet exposure, asset criticality, and
  patch availability. Emits a **P1–P4** priority with a full `rationale` list so the decision
  is transparent. A high-severity, actively-exploited vulnerability is always P1.

## 3. Detection authoring (UC-04)

`dula_ai.intel.detections.sigma`, `...yara`, `...coverage`.

- **Sigma** and **YARA** rules are **authored deterministically** from extracted indicators and
  **always validated before return**, so generated rules are syntactically valid and reviewable
  (the Phase 05 acceptance criterion). Emitters are dependency-free (no PyYAML), preserving the
  air-gapped guarantee.
- **Validators** (`validate`, `validate_text`) enforce the grammar a SIEM/scanner relies on:
  required keys, a non-empty logsource, selection blocks, and a `condition` that references
  only defined identifiers (Sigma); a valid rule identifier, balanced braces, a `condition`,
  and defined string references (YARA). `validate_text` grades an **externally-supplied**
  (e.g. model-drafted) rule — invalid rules are rejected, never emitted.
- **ATT&CK coverage** (`coverage.coverage`) — maps a detection set's tags to techniques and
  tactics, and reports gaps and a coverage ratio against a target technique set. A parent
  technique covers its sub-technique targets.

## 4. Evaluation gates (`dula_ai.intel.benchmark`)

Per "evaluation gates everything" ([EvaluationStrategy.md](./EvaluationStrategy.md)), fixed
labelled suites run offline in CI ([Benchmarking.md](./Benchmarking.md)):

- **CTI extraction** — IOC + technique precision/recall over curated advisories; baselines are
  asserted in `test_intel_benchmark.py`.
- **Detection authoring** — every authored Sigma and YARA rule must be syntactically valid
  (100%).
- **Red-team / dual-use** (`test_intel_redteam.py`) — indirect prompt injection embedded in an
  advisory is flagged and not obeyed; secret-like content the model might echo is redacted;
  oversized advisories are rejected.

## 5. API surface

Exposed under `/api/v1/intel` by `apps/ai-gateway` (per-action OPA authorization —
`ai.cti`, `ai.vuln`, `ai.detect`). See
[../12-API/AIGatewayAPI.md](../12-API/AIGatewayAPI.md) for request/response contracts. `apps/web`
adds an **Intel workbench** page (`/intel`) — server-proxied calls, same authz — covering all
three capabilities; see
[../17-User-Documentation/CyberIntelligenceUserGuide.md](../17-User-Documentation/CyberIntelligenceUserGuide.md).

## Maturity & limits

- The ATT&CK catalog and IOC/TTP heuristics are **curated**, not exhaustive; full-feed
  ingestion and semantic TTP mapping are FUTURE.
- Offline, the CTI summary is extractive (deterministic); a served Dula AI / Ollama model
  produces richer summaries behind the gateway with no API change.
- Rule authoring covers IOC-driven detections; behavioural/complex-logic authoring is FUTURE.
