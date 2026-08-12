---
title: Knowledge Source Registry
document_id: AI-014
status: Draft
version: 0.1.0
last_updated: 2026-08-12
owner: AI
audience: AI Engineer, Security Engineer, Operator
phase: Phase 03 — Knowledge & RAG (M003)
related:
  - ./DatasetStrategy.md
  - ../03-Architecture/RAGArchitecture.md
  - ../16-Operations/RAGRunbook.md
---

# Knowledge Source Registry

> **Purpose.** Track the public knowledge sources ingested into the shared RAG corpus, with
> their licenses. Ingestion enforces a **license allowlist** for public knowledge; a source
> not on an allowlisted license is rejected (T3/T4 — poisoning & licensing).

## Public sources

| Source key | Content | License | Status |
|------------|---------|---------|--------|
| `mitre-attack` | ATT&CK techniques/mitigations | MITRE-ATT&CK terms | Registered; demo subset seeded |
| `nvd-cve` | CVE records / advisories | public-domain | Registered; demo subset seeded |
| `cisa-kev` | CISA Known Exploited Vulns / guidance | public-domain | Registered; demo subset seeded |
| `sigma-rules` | Sigma detection rules | CC-BY-4.0 | Registered (FUTURE ingestion) |

The **demo corpus** (`dula_ai.corpus`) contains short illustrative paraphrases of the above
so RAG, the demo, and the benchmark run fully offline. Ingestion of full upstream feeds is
**FUTURE**, governed by [./DatasetStrategy.md](./DatasetStrategy.md).

## License allowlist (public knowledge)

`MIT`, `Apache-2.0`, `BSD-3-Clause`, `CC0-1.0`, `CC-BY-4.0`, `CC-BY-SA-4.0`,
`MITRE-ATT&CK`, `public-domain`. Enforced in `dula_ai.knowledge` (`PUBLIC_ALLOWED_LICENSES`).
Tenant-private data is the tenant's own and is not license-gated.

## Provenance & purge

Every chunk records `source`, `license`, `embedding_model`, and `ingested_at`. A source can
be purged from all indices (`DELETE /api/v1/knowledge/sources/{source}`) if it is found to be
poisoned or its license status changes — see
[../16-Operations/RAGRunbook.md](../16-Operations/RAGRunbook.md).

## Adding a source

1. Confirm license is allowlisted (or add via a reviewed change with legal sign-off).
2. Register the source key here with content + license.
3. Ingest with correct `source`/`license`/`classification`; verify with the benchmark.
