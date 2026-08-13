---
title: Project Context (Long-Lived Knowledge)
document_id: CTX-000
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Engineering leadership
audience: All contributors (and future context recovery)
phase: Documentation Bootstrap (M000)
---

# PROJECT_CONTEXT

> **Purpose.** Durable, slowly-changing knowledge about the project. Read this first to
> recover context. For *current execution state*, see [PROJECT_STATE.md](./PROJECT_STATE.md).

## 1. What We Are Building

Two integrated but independently deployable products:
- **Dula Platform** (Product 1) — enterprise cybersecurity AI platform.
- **Dula AI** (Product 2) — cybersecurity-specialized LLM + training/eval/serving stack.

See [02-Vision/Vision.md](./02-Vision/Vision.md). Names are **decided** (ADR-0001,
Accepted): *Dula* is from the Oromo language (*Duulaa* = warrior/knight; *Abbaa Duulaa* =
war leader / defense commander).

## 2. Core Principles (durable)

Defensive-only & ethical · data sovereignty (air-gapped capable) · grounded/cited/auditable
AI · human-in-command for consequential actions · security by design · deploy-anywhere from
one codebase · honesty about maturity · incremental delivery · open/portable/minimal ·
reproducibility. See [02-Vision/GuidingPrinciples.md](./02-Vision/GuidingPrinciples.md).

## 3. Technology Baseline (candidates, ADR-gated)

Python 3.12/FastAPI (primary) + Go (data-plane) · TypeScript/Next.js · PostgreSQL 16 ·
**Qdrant** (vectors) · **OpenSearch** (BM25 + log-analytics) · Redis · **Redpanda (Kafka
API)** event backbone · MinIO/S3 · vLLM + llama.cpp · Keycloak/OIDC + OPA · Kubernetes/Helm
+ Argo CD · MLflow + DVC + Argo Workflows · OTel + Prometheus/Grafana/Loki/Tempo · Vault +
SOPS · Terraform. These are **permanent, production-grade** choices (not MVP placeholders).
Full rationale & alternatives: [01-Project/TechnologyStack.md](./01-Project/TechnologyStack.md).

## 4. Architecture Essentials (durable)

- Model-agnostic **LLM gateway** is the single AI choke point (guardrails/quotas/audit).
- **RAG** grounds answers; all retrieved/model/tool content is **untrusted**.
- **Agents** are permissioned, human-approved for consequential actions, fully audited.
- **Plugins/connectors** are sandboxed, signed, least-privilege, default-deny egress.
- **Multi-tenancy** = app scope + Postgres RLS + index namespacing (defense-in-depth).
- **Deploy-anywhere** via Helm value overlays; air-gapped uses a signed offline bundle.
See [03-Architecture/](./03-Architecture/SystemArchitecture.md).

## 5. AI Strategy Essentials (durable)

Staged progression (open model → prompting → RAG → tools → datasets → **benchmark** →
tuning → LoRA/QLoRA → quantization → optimization → distillation → specialized → advanced →
pretraining). **Evaluation gates everything**; climb stages only when justified. From-scratch
pretraining is RESEARCH/likely-never. See [08-AI/DulaAIStrategy.md](./08-AI/DulaAIStrategy.md).

## 6. Architecture Decisions (RESOLVED in M000 review)

ADR-0001…0010 are **Accepted and permanent** (see [adr/README.md](./adr/README.md) and
[PROJECT_REVIEW-M000.md](./PROJECT_REVIEW-M000.md)): Dula/Dula AI naming · Python/FastAPI
primary + Go for data-plane · **Qdrant** (vectors) + **OpenSearch** (BM25/log-analytics) ·
**Redpanda (Kafka API)** event backbone · vLLM+llama.cpp · logical multi-tenancy **+
mandatory AI-layer isolation** · **Apache-2.0 base models (Qwen/Mistral); Llama
deprioritized** · **agents built on LangGraph** + first-party security layer · Keycloak+OPA
· MLflow+DVC+Argo. These are production-grade, not MVP staging; ADR-0002/0003/0004 were
revised during M000 to their permanent form.

**Also decided:** repository model = **monorepo `dula`** (ADR-0011). **Dula AI training compute &
artifact hosting** = free GPU (Kaggle/Lightning/Modal) + Hugging Face Hub for datasets/models,
keeping GitHub for code/CI (ADR-0012); Primus (ODC-BY/MIT) datasets; QLoRA on Qwen/Mistral.

**Still open:** API gateway tech · embedding/reranker model · hardware sizing · SLSA level.
(Plugin sandbox mechanism is now **DECIDED — ADR-0013**.)

## 7. Key Risks (durable watchlist)

- Ingestion throughput on Python (→ Go data-plane / Kafka if needed).
- GPU availability in on-prem/air-gapped (→ quantized CPU serving fallback).
- RAG/data poisoning & prompt injection (→ untrusted-content model, provenance).
- Agent safety / privilege escalation (→ permissions + approval + eval gates).
- Dataset/model licensing (→ license gate; **REQUIRES RESEARCH** per source).
- Scope breadth vs delivery (→ strict phase sequencing).
See [03-Architecture/ArchitectureRoadmap.md](./03-Architecture/ArchitectureRoadmap.md).

## 8. Requires Research (still unverified — empirical/measure-later)

Embedding/reranker model choice · OpenSearch vs ClickHouse (log analytics) · OCSF/ECS/STIX
schema alignment · hardware sizing for training/inference · benchmark composition/thresholds
· SLSA target level. These are **not** asserted as fact anywhere.

*(Resolved in M000 review: base-model licensing — ADR-0007 fixes Apache-2.0 Qwen/Mistral as
the candidate set; OWASP LLM Top 10 : 2025 pinned in the AI threat model.)*

## 9. How to Use the Docs

Handbook guide: [README.md](./README.md); full index: [SUMMARY.md](./SUMMARY.md);
standards: [00-Governance/](./00-Governance/DocumentationStandards.md).

**Documentation lifecycle (mandatory).** Every milestone and phase closes under
**CLAUDE.md §11**: technical docs (areas `00`–`16`) **and** user/operator docs
([17-User-Documentation/](./17-User-Documentation/README.md)) are part of the Definition of
Done. Closure artifacts (Milestone Closure Reports, Phase Completion Reviews) live in
[04-MVP-Roadmap/closure/](./04-MVP-Roadmap/closure/README.md); a milestone is
`DOCUMENTATION-INCOMPLETE` (not `COMPLETE`) if required docs are missing.

## 10. Boundary

Implementation is underway: **Phases 01 (M001) through 07 (M007) are complete and closed**
(see [PROJECT_STATE.md](./PROJECT_STATE.md) and
[04-MVP-Roadmap/closure/](./04-MVP-Roadmap/closure/README.md)). Phase 02 delivered the core
domain (assets/alerts/incidents + audit), the Redpanda event backbone + worker, service-layer
OPA authorization, tenant-isolation baseline, and an authenticated UI shell. Phase 03 delivered
the **first shippable MVP**: the model-agnostic LLM Gateway, the RAG subsystem (hybrid
retrieval with tenant filtering, citations, guardrails), the AI Gateway service (grounded Q&A +
triage with streaming), an evaluation benchmark, and AI red-team basics — all running fully
offline on a general model. **Phase 04 (Dula AI)** has its train→eval→**gate**→register→serve
pipeline delivered and CI-green (torch-free `packages/dula-ml` + standalone `ml/` GPU project +
OpenAI-compatible serving + ADR-0012). **Phase 04 is complete:** a real QLoRA candidate
(Qwen2.5-0.5B on Primus) was trained + evaluated vs the general model on free compute and
**retired** by the gate (didn't beat quality, regressed safety) — so the platform stays on the
general model + RAG (acceptance met on the retire outcome; a worse model never ships).
**Phase 05 (Cyber Intelligence) is complete:** a deterministic, offline-first intelligence
core (`dula_ai.intel`) delivers CTI extraction (IOC/TTP + STIX 2.1), CVSS v3.1 scoring with
explainable P1–P4 prioritization, and Sigma/YARA authoring with always-validated output plus
ATT&CK coverage mapping — exposed via `apps/ai-gateway` `/api/v1/intel/*` and an `apps/web`
Intel workbench page, gated by domain benchmark and red-team/dual-use safety suites. The
extraction and rule-authoring are deliberately **deterministic, not model-dependent**, so
their outputs are explainable, reproducible, and air-gapped by default; a model is used only
for the optional, guardrailed CTI summary. **Phase 06 (Agents) is complete:** a first-party
**agent runtime** (`packages/dula-agents`, ADR-0008) owns the security-critical layer — the
planner only proposes, and the runtime executes a step only after it passes the agent's tool
allowlist, the invoking user's OPA authorization (**agent ⊆ user**), and (for consequential
tools) **human approval**, all under step/cost/time limits and full audit. The **investigation
assistant** (UC-03) works an alert with read-first tools and gates its recommended ticket on
approval; a **release-blocking safety suite** proves zero unauthorized actions under adversarial
conditions. It is exposed via `/api/v1/agents/*` and an `apps/web` Agents page; the planner is
deterministic/offline today (LangGraph or a model planner can back it later behind the same
interface). **Phase 07 (Integrations) is complete:** a **signed, sandboxed** plugin/connector
framework (`packages/dula-plugins`) connects Dula to external systems — Ed25519 manifest signing
+ trust/revocation, a **default-deny egress allowlist with SSRF** protection, and a host that
verifies-on-install, grants only manifest-declared permissions, OPA-authorizes every capability
call, bounds resources, and treats output as untrusted. First connectors (SIEM search, TI
lookup, ticketing create) are fixture-backed offline, with the investigation agent's log-search
and ticket-creation tools now **connector-backed** (agent→connector; ticket approval-gated).
Air-gapped-first: egress is disabled by default, so live-feed connectors are inert with no
phone-home. The **sandbox mechanism is DECIDED (ADR-0013)** — an out-of-process worker with
host-brokered capabilities (no ambient network) as the portable baseline + a container per
orchestrated profile, behind a pluggable `SandboxRunner`; the in-process default is delivered and
the OS-level worker runners are FUTURE. Subsequent phases proceed per the roadmap and the §11
closure lifecycle; a phase begins only when directed.
