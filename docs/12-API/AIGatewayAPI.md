---
title: AI Gateway API (Grounded Q&A, Triage, Knowledge)
document_id: API-005
status: Draft
version: 0.2.0
last_updated: 2026-08-13
owner: AI / Backend
audience: Developer, API consumer
phase: Phase 05 — Cyber Intelligence (M005)
related:
  - ./Authentication.md
  - ./Authorization.md
  - ../03-Architecture/AIArchitecture.md
  - ../03-Architecture/RAGArchitecture.md
  - ../08-AI/RAGEngineering.md
  - ../08-AI/CyberIntelligence.md
  - ../16-Operations/RAGRunbook.md
  - ../17-User-Documentation/AskDulaUserGuide.md
  - ../17-User-Documentation/CyberIntelligenceUserGuide.md
---

# AI Gateway API

> **Purpose.** Reference for the Phase 03 AI endpoints served by **`apps/ai-gateway`**:
> grounded Q&A (UC-14), alert triage (UC-01), and tenant-private knowledge ingestion. All
> AI consumption goes through the model-agnostic **LLM Gateway**. **Status: CURRENT**
> (default offline profile). User guide:
> [../17-User-Documentation/AskDulaUserGuide.md](../17-User-Documentation/AskDulaUserGuide.md).

## Conventions

- Base path `/api/v1`; every endpoint requires a Keycloak bearer token
  ([Authentication.md](./Authentication.md)). Missing/invalid → **401**; missing `tenant_id`
  claim → **403**.
- Authorization is enforced per action via OPA before the handler runs (fail-closed); a
  denied action → **403** ([Authorization.md](./Authorization.md)).
- Retrieval is **tenant-scoped**: a caller only ever sees their tenant's knowledge plus
  shared `public` knowledge — never another tenant's (ADR-0006 / OWASP LLM08).
- **All retrieved content and model output are untrusted**; answers are grounded and must
  cite evidence. Per-tenant token budgets apply (exceeding → **429**).

## Endpoints

| Method & path | Action (OPA) | Purpose |
|---------------|--------------|---------|
| `POST /api/v1/ask` | `ai.ask` | Grounded Q&A; returns answer + citations + usage |
| `POST /api/v1/ask/stream` | `ai.ask` | Same, streamed as Server-Sent Events (for chat UIs) |
| `POST /api/v1/triage` | `ai.triage` | Grounded triage of an alert (title/severity/details) |
| `POST /api/v1/knowledge/documents` | `knowledge.ingest` | Ingest a **tenant-private** document |
| `DELETE /api/v1/knowledge/sources/{source}` | `knowledge.purge` | Purge all chunks from a source (poison response) |
| `POST /api/v1/intel/extract` | `ai.cti` | CTI: extract IOCs/TTPs + STIX bundle (+ optional summary) |
| `POST /api/v1/intel/vulnerability` | `ai.vuln` | Vulnerability: CVSS score + P1–P4 prioritization |
| `POST /api/v1/intel/detections/sigma` | `ai.detect` | Author a validated Sigma rule from an advisory |
| `POST /api/v1/intel/detections/yara` | `ai.detect` | Author a validated YARA rule from an advisory |
| `POST /api/v1/intel/detections/validate` | `ai.detect` | Validate an external Sigma/YARA rule |
| `POST /api/v1/intel/detections/coverage` | `ai.detect` | ATT&CK coverage of a detection set vs a target |
| `GET /healthz`, `GET /readyz` | — | Probes |

## Cyber-intelligence endpoints (Phase 05)

The `/api/v1/intel/*` endpoints deliver CTI extraction (UC-05), vulnerability analysis
(UC-07), and detection authoring (UC-04). The heavy lifting is **deterministic and offline**;
only the optional CTI summary uses the LLM Gateway. All authored rules are **validated before
return**. Full capability reference:
[../08-AI/CyberIntelligence.md](../08-AI/CyberIntelligence.md).

- `POST /intel/extract` — body `{"advisory": "...", "summarize": true}` → `{indicators[],
  techniques[], stix_bundle, summary, input_flags[]}`. Indicators are **defanged**; the STIX
  bundle is a deterministic STIX 2.1 document. Empty/oversized advisory → **400**.
- `POST /intel/vulnerability` — body `{"cvss_vector": "CVSS:3.1/AV:N/...", "known_exploited":
  true, "internet_facing": true, "asset_criticality": "high", "patch_available": false}` →
  `{base_score, severity, priority, risk_score, rationale[], metrics}`. Malformed vector → **400**.
- `POST /intel/detections/sigma` and `.../yara` — body includes `advisory` (+ Sigma
  `category`/`product`/`service`, `attack_tags`, `level`; YARA `name`, `tags`) → `{rule, valid,
  errors[], warnings[]}`. No usable indicators → **422**.
- `POST /intel/detections/validate` — body `{"format": "sigma"|"yara", "rule": "..."}` →
  `{valid, errors[]}` for an externally-supplied (e.g. model-drafted) rule.
- `POST /intel/detections/coverage` — body `{"rule_tag_sets": [["attack.t1071"], ...], "target":
  ["T1071", ...]}` → `{covered_techniques[], covered_tactics[], gaps[], coverage_ratio}`.

## Answer shape

```json
{
  "answer": "Based on the retrieved evidence: … [1] …",
  "grounded": true,
  "model": "extractive-v1",
  "prompt_version": "grounded-qa/v1",
  "citations": [
    {"marker": 1, "source": "mitre-attack", "document_id": "attack-t1110", "snippet": "…"}
  ],
  "usage": {"prompt_tokens": 120, "completion_tokens": 40, "total_tokens": 160}
}
```

- `grounded` is `false` when no supporting evidence was found — the answer then states it
  lacks information (no hallucinated citations).
- Streaming (`/ask/stream`) emits `data: {"token": "…"}` events, then a final
  `event: done` whose `data` is the full answer object above.

## Examples

```bash
TOKEN=...  # Keycloak access token (aud: dula-api)

# Grounded Q&A
curl -sX POST http://localhost:8100/api/v1/ask \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"question":"How do I defend against brute force attacks?"}'

# Ingest a tenant-private note
curl -sX POST http://localhost:8100/api/v1/knowledge/documents \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"text":"Our honeypot is host HP-7.","source":"runbook"}'
```

## Profiles & models

- **offline** (default): in-memory stores + `extractive-v1` provider + hashing embedder —
  fully air-gapped, no downloads (Acceptance: works offline).
- **backed**: Qdrant (vectors) + OpenSearch (BM25) + optional Ollama provider/embeddings.

Selection and budgets are configuration, not code (ADR-0005). The Dula AI model (Product 2)
will be served behind this same gateway without endpoint changes.

## Auditing

Every AI call emits a structured audit log and an `ai.query.completed` event (tenant, actor,
task, model, tokens, cached, input flags). **No prompt or answer content is logged** (T5/T13).
