---
title: Naming Conventions
document_id: GOV-004
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Engineering Governance
audience: All contributors
phase: Documentation Bootstrap (M000)
related:
  - ./CodingStandards.md
  - ../01-Project/ProjectStructure.md
---

# Naming Conventions

> **Purpose.** Provide one authoritative set of naming rules for everything the project
> produces, so names are predictable and greppable across code, data, and infrastructure.

## 1. Documents

- Document files: `PascalCase.md` within numbered area folders (e.g.
  `SystemArchitecture.md`).
- `document_id` prefixes (front-matter): fixed per area.

| Prefix | Area |
|--------|------|
| GOV | 00-Governance |
| PRJ | 01-Project |
| VIS | 02-Vision |
| ARC | 03-Architecture |
| MVP | 04-MVP-Roadmap |
| BE | 05-Backend |
| FE | 06-Frontend |
| DB | 07-Database |
| AI | 08-AI |
| MLO | 09-MLOps |
| SEC | 10-Security |
| DEP | 11-Deployment |
| API | 12-API |
| AGT | 13-Agents |
| PLG | 14-Plugins |
| TST | 15-Testing |
| OPS | 16-Operations |
| USR | 17-User-Documentation |

Lifecycle-closure artifacts live in `04-MVP-Roadmap/closure/` (see **CLAUDE.md §11**):
Milestone Closure Reports `M0NN-<slug>-Closure.md` (`document_id: MVP-M0NN-CLOSURE`) and
Phase Completion Reviews `PhaseNN-<slug>-Completion-Review.md` (`document_id: MVP-PNN-COMPLETION`).

## 2. Files & Directories (Code)

- Directories and Python modules: `snake_case`.
- Python packages: `snake_case`; classes `PascalCase`; functions/vars `snake_case`;
  constants `UPPER_SNAKE_CASE`.
- TypeScript files: `kebab-case.ts` for modules, `PascalCase.tsx` for React components.
- Test files: `test_*.py` (Python), `*.test.ts` / `*.spec.ts` (TypeScript).

## 3. Code Identifiers

- Booleans read as predicates: `is_enabled`, `has_access`, `can_execute`.
- Avoid abbreviations except well-known ones (`id`, `url`, `db`, `llm`, `rag`).
- Domain terms match the [Glossary](../01-Project/Glossary.md) exactly.

## 4. APIs

- REST paths: `kebab-case`, plural nouns: `/api/v1/threat-intel/indicators`.
- Query params & JSON fields: `snake_case`.
- Versioning in the path: `/api/v{major}/...` (see [../12-API/Versioning.md](../12-API/Versioning.md)).
- Event names: `domain.entity.action` (e.g. `ingest.log.received`, `agent.run.completed`).

## 5. Databases

- Tables: `snake_case`, plural (`incidents`, `threat_indicators`).
- Columns: `snake_case`; primary key `id`; foreign keys `<entity>_id`.
- Timestamps: `created_at`, `updated_at`, `deleted_at` (UTC).
- Every tenant-scoped table includes `tenant_id`.
- Indexes: `ix_<table>_<cols>`; unique: `uq_<table>_<cols>`; FKs: `fk_<table>_<ref>`.

## 6. Containers & Images

- Image names: `dula/<component>` (e.g. `dula/api-gateway`, `dula/llm-gateway`).
- Tags: semver + git sha (`1.4.2`, `1.4.2-abc1234`); never rely on `latest` in
  production.

## 7. Kubernetes

- Namespaces: `dula-<env>` (e.g. `dula-prod`, `dula-staging`).
- Workloads: `<component>` (e.g. `api-gateway`, `rag-service`).
- Labels: `app.kubernetes.io/name`, `app.kubernetes.io/component`,
  `app.kubernetes.io/part-of: dula`.
- Helm releases: `dula-<component>` or a single umbrella `dula`.

## 8. Models (Dula AI & Embeddings)

- Model artifact name: `dula-<base>-<task>-<method>-v<major.minor>`
  e.g. `dula-qwen2_5-7b-instruct-lora-v0.1`.
- Registry stage tags: `staging`, `production`, `archived` (see
  [../09-MLOps/ModelRegistry.md](../09-MLOps/ModelRegistry.md)).
- Quantized variants append the scheme: `...-awq4`, `...-gguf-q4_k_m`.

## 9. Datasets

- Dataset name: `<domain>-<purpose>-v<major.minor>`
  e.g. `attack-technique-qa-v0.3`, `sigma-rule-corpus-v1.0`.
- Every dataset version is immutable and tracked (see
  [../09-MLOps/DatasetVersioning.md](../09-MLOps/DatasetVersioning.md)).
- Splits: `train`, `validation`, `test`, `eval` (eval = benchmark, held out).

## 10. Agents

- Agent identifier: `snake_case` role name (`soc_triage_agent`, `threat_hunt_agent`).
- Tools: `verb_noun` (`search_logs`, `enrich_indicator`, `create_ticket`).
- Agent runs get a ULID `run_id`.

## 11. Plugins & Connectors

- Plugin id: `dula-plugin-<vendor>-<product>` (e.g. `dula-plugin-splunk`,
  `dula-plugin-virustotal`).
- Connector capability names: `<system>.<capability>` (`splunk.search`, `vt.lookup_hash`).

## 12. Environments

- Canonical environment names: `dev`, `test`, `staging`, `prod`, plus deployment
  *profiles* `onprem`, `airgapped`, `cloud`, `hybrid` (see
  [../11-Deployment/README.md](../11-Deployment/README.md)).

## Related Documents

- [../01-Project/ProjectStructure.md](../01-Project/ProjectStructure.md)
- [./CodingStandards.md](./CodingStandards.md)
