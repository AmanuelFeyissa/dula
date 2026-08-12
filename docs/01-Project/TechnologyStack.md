---
title: Technology Stack
document_id: PRJ-003
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Architecture
audience: Architects, engineers, ops
phase: Documentation Bootstrap (M000)
related:
  - ../03-Architecture/SystemArchitecture.md
  - ../00-Governance/ArchitectureDecisionRecords.md
---

# Technology Stack

> **Purpose.** Record each major technology choice with alternatives considered, the
> reason for selection, and risks. These are the project's **permanent, production-grade**
> choices (accepted via ADRs —
> [../00-Governance/ArchitectureDecisionRecords.md](../00-Governance/ArchitectureDecisionRecords.md));
> they are not MVP placeholders to be migrated later, and change only if a materially better
> technology emerges (via a new/superseding ADR). Selections weigh: performance, security,
> licensing, community, maintainability, cloud + on-prem + **air-gapped** support,
> Kubernetes fit, developer experience, and operational complexity.

> **Guiding constraint.** The platform must run **air-gapped and offline**. This biases
> every choice toward **self-hostable, permissively licensed, open-source** components and
> against managed-only SaaS or restrictive licenses.

## 1. Selection Summary

> **All ADRs below are Accepted and permanent** (see [../adr/README.md](../adr/README.md)).
> "Selected" = the standing decision; rationale is in §2.

| Layer | Selected | Key alternatives | ADR |
|-------|----------|------------------|-----|
| Backend language | Python 3.12 primary + Go (data-plane) | Node/TS, Rust | ADR-0002 ✅ |
| API framework | FastAPI | Django REST, Litestar, Flask | ADR-0002 ✅ |
| Frontend | Next.js + React + TS | SvelteKit, Remix, plain React SPA | — |
| Relational DB | PostgreSQL 16 | MySQL, CockroachDB | — |
| Vector DB | **Qdrant** | pgvector, Milvus, Weaviate | ADR-0003 ✅ |
| Search / log-analytics | **OpenSearch** (BM25 + analytics) | Elasticsearch, ClickHouse | ADR-0003 ✅ |
| Cache | Redis | Valkey, KeyDB | — |
| Event & streaming backbone | **Redpanda (Kafka API)** | Apache Kafka, RabbitMQ, NATS | ADR-0004 ✅ |
| Object storage | MinIO (S3 API) | Ceph, cloud S3 | — |
| LLM serving | vLLM (GPU) + llama.cpp (CPU) + Ollama (dev) | TGI, TensorRT-LLM | ADR-0005 ✅ |
| LLM gateway | Custom (LiteLLM-informed) | LiteLLM as-is, direct SDKs | ADR-0005 ✅ |
| Embeddings | Open models (bge/e5/gte family — tune via eval) | Proprietary embedding APIs | ADR-0007 ✅ / research |
| Agent orchestration | **LangGraph + first-party security layer** | custom, CrewAI, AutoGen | ADR-0008 ✅ |
| Base model family | **Apache-2.0 (Qwen/Mistral)**; Llama deprioritized | Gemma/Phi | ADR-0007 ✅ |
| AuthN | Keycloak (OIDC/OAuth2) | Ory, Authentik, Auth0 | ADR-0009 ✅ |
| AuthZ policy | OPA / Rego | Casbin, Cedar, app-native | ADR-0009 ✅ |
| API gateway tech | **REQUIRES DECISION** (Envoy vs FastAPI edge) | Kong, APISIX | — |
| Orchestration | Kubernetes + Helm | Nomad, Docker Swarm | — |
| GitOps/CD | Argo CD | Flux, manual Helm | — |
| MLOps | MLflow + DVC + Argo Workflows | W&B, ClearML, LakeFS, Kubeflow | ADR-0010 ✅ |
| Observability | OpenTelemetry + Prometheus + Grafana + Loki + Tempo | ELK, Datadog | — |
| Secrets | HashiCorp Vault + SOPS | Sealed Secrets, cloud KMS | — |
| IaC | Terraform + Helm | Pulumi, Ansible | — |
| CI/CD | GitHub Actions (+ self-hosted runners) | GitLab CI, Jenkins | — |

## 2. Rationale by Choice

### 2.1 Backend: Python 3.12 + FastAPI (primary) with Go (data-plane) — **ADR-0002**
- **Why:** AI/ML ecosystem is Python-native (PyTorch, transformers, PEFT, vLLM); FastAPI
  gives async performance, first-class OpenAPI, and Pydantic validation. Python is the
  **permanent primary** language for services, APIs, AI, and pipelines.
- **Go (permanent secondary):** an **approved** language for high-throughput data-plane
  components (e.g. the telemetry ingestion pipeline) where measured throughput warrants it
  — a standing part of the polyglot architecture, not a deferral (see
  [../00-Governance/CodingStandards.md](../00-Governance/CodingStandards.md) §4).
- **Alternatives:** Node/TS (would fragment the ML story); Rust (reserved for rare proven
  hot paths only).
- **Boundaries:** bounded contexts behind clear APIs let a Go data-plane service coexist
  cleanly with the Python core.

### 2.2 Frontend: Next.js + React + TypeScript
- **Why:** Mature ecosystem, SSR/streaming for responsive AI UIs, strong typing,
  self-hostable, works offline/air-gapped when built as a static/standalone server.
- **Alternatives:** SvelteKit (leaner but smaller talent pool), Remix, plain SPA (loses
  SSR/streaming benefits for chat/agent UIs).
- **Risks:** Framework churn; mitigate by keeping business logic in the API, not the UI.

### 2.3 Relational DB: PostgreSQL 16
- **Why:** Reliable, feature-rich (JSONB, RLS for tenant isolation, `pgvector` available),
  permissive license, ubiquitous on-prem and cloud, strong K8s operators.
- **Alternatives:** MySQL (weaker JSON/extension story), CockroachDB (distributed but
  heavier ops, licensing considerations).
- **Note:** Row-Level Security supports the multi-tenancy model (see
  [../03-Architecture/SystemArchitecture.md](../03-Architecture/SystemArchitecture.md)).

### 2.4 Vector DB: Qdrant — **ADR-0003 (Accepted)**
- **Decision:** **Qdrant** is the platform's standard vector store from day one.
- **Why:** purpose-built ANN, Rust performance, Apache-2.0, rich payload filtering,
  K8s-friendly, air-gap capable — the permanent production choice.
- **Note:** PostgreSQL remains the relational system of record; `pgvector` is **not** the
  platform vector store. The `rag-service` still abstracts the store so a future swap is
  possible only if a materially better engine emerges.

### 2.5 Search / Log-Analytics: OpenSearch — **ADR-0003 (Accepted)**
- **Decision:** **OpenSearch** is the standard lexical/full-text engine (BM25) and
  security-log analytics store. **Hybrid retrieval = Qdrant (vectors) + OpenSearch (BM25)**.
- **Why:** Apache-2.0, mature full-text + log analytics fit for a security product,
  self-hostable/air-gap capable.
- **Alternatives:** Elasticsearch (product-embedding license concerns); ClickHouse
  (analytics-oriented) — **not adopted**.

### 2.6 Event & Streaming Backbone: Redpanda (Kafka API) — **ADR-0004 (Accepted)**
- **Decision:** **Redpanda (Kafka-compatible)** is the permanent event & streaming backbone
  for all async events, high-volume telemetry ingestion, and agent/domain events. **Apache
  Kafka** is an accepted drop-in equivalent (same Kafka API).
- **Why:** SIEM-scale throughput + durable replay + consumer groups, single-binary (no
  ZooKeeper/JVM), low ops, strong air-gapped footprint.
- **Note:** a single backbone is used; synchronous request/reply uses REST/gRPC, not the
  bus. Event naming `domain.entity.action`; consumers idempotent.

### 2.7 LLM Serving: vLLM + llama.cpp
- **Why:** vLLM offers high-throughput GPU inference (paged attention, continuous
  batching); llama.cpp/GGUF covers CPU-only, edge, and air-gapped low-resource cases.
- **Alternatives:** HF TGI, Ollama (great DX, wraps llama.cpp), TensorRT-LLM (max GPU
  perf, NVIDIA-locked, complex). Ollama is a strong **developer-experience** choice for
  local/dev and small on-prem.
- **Risks:** GPU availability in on-prem/air-gapped installs; the CPU path (llama.cpp +
  quantized models) is the fallback. See [../08-AI/InferenceArchitecture.md](../08-AI/InferenceArchitecture.md).

### 2.8 Agent Orchestration: LangGraph + first-party security layer — **ADR-0008 (Accepted)**
- **Decision:** **build on LangGraph** for the plan/act graph, checkpointing, and
  human-in-the-loop pause/resume, and implement the **security-critical layer** (tool
  permission checks, approval broker, audit, step/loop/time/cost limits) as **first-party
  Dula code**. This avoids re-implementing solved plumbing (M000 review O3) while keeping
  security controls owned and testable.
- **Alternatives:** fully custom (over-engineering), CrewAI/AutoGen (less execution control).
- **Note:** the agent-runtime interface abstracts LangGraph so it can be replaced; verify
  its license at adoption. See [../03-Architecture/AgentArchitecture.md](../03-Architecture/AgentArchitecture.md).

### 2.9 Auth: Keycloak (OIDC) + OPA (Rego)
- **Why:** Keycloak is a mature, self-hostable IdP (OIDC/SAML, federation, MFA); OPA
  externalizes authorization policy for RBAC/ABAC consistently across services.
- **Alternatives:** Ory/Authentik (lighter), Cedar/Casbin (policy). Auth0 excluded
  (SaaS-only conflicts with air-gapped requirement).

### 2.10 Orchestration & Delivery: Kubernetes + Helm + Argo CD
- **Why:** Portable across cloud/on-prem/air-gapped; Helm packages every profile; Argo CD
  gives GitOps. Docker Compose covers local dev.
- **Alternatives:** Nomad (simpler but smaller ecosystem), Swarm (declining).

### 2.11 MLOps: MLflow + DVC + Argo Workflows
- **Why:** All self-hostable and open-source; MLflow for tracking/registry, DVC for
  dataset/versioning over object storage, Argo for pipeline orchestration on K8s.
- **Alternatives:** W&B/ClearML (excellent, but SaaS-leaning or heavier for air-gap),
  LakeFS (data versioning at scale — candidate if DVC scaling is insufficient),
  Kubeflow (powerful but heavy). See [../09-MLOps/README.md](../09-MLOps/README.md).

### 2.12 Observability: OpenTelemetry + Prometheus/Grafana/Loki/Tempo
- **Why:** Vendor-neutral instrumentation (OTel), metrics (Prometheus), dashboards
  (Grafana), logs (Loki), traces (Tempo). Fully self-hostable and air-gap capable.

### 2.13 Secrets: Vault + SOPS
- **Why:** Vault for dynamic secrets and encryption-as-a-service; SOPS for encrypted
  config in Git (GitOps-friendly). See [../10-Security/DataSecurity.md](../10-Security/DataSecurity.md).

### 2.14 Base Model Family: Apache-2.0 (Qwen/Mistral) — **ADR-0007 (Accepted)**
- **Decision:** prefer **Apache-2.0 open-weight families (Qwen, Mistral)** as the primary
  base-model candidates. Research (Aug 2026) confirmed most Qwen and much of Mistral ship
  under **Apache-2.0** (clean commercial/self-host/redistribution/fine-tune), whereas
  **Llama** uses Meta's **Community License** (acceptable-use policy, derivative-naming rule,
  large-platform commercial threshold, EU/regional multimodal restrictions) — a real risk
  for an air-gapped, redistributable product. Llama is therefore deprioritized for the core.
- **Final checkpoint/size** is chosen empirically by the internal benchmark; model-weight
  **provenance/hashes are verified on load** (supply chain). See
  [../08-AI/ModelSelection.md](../08-AI/ModelSelection.md) and
  [../adr/ADR-0007-base-model.md](../adr/ADR-0007-base-model.md).

## 3. Cross-Cutting Constraints Checklist

| Requirement | How the stack satisfies it |
|-------------|----------------------------|
| Air-gapped | Every component is self-hostable OSS; models run locally (vLLM/llama.cpp) |
| On-prem | K8s + Helm; no managed-only dependencies in the core |
| Cloud | Same charts; managed equivalents optional, not required |
| Licensing | Permissive/OSS bias; license gate in CI ([Dependencies.md](./Dependencies.md)) |
| Security | Keycloak/OPA, Vault, OTel audit, sandboxed plugins/agents |
| K8s | All core components have operators/charts |

## 4. Open Technology Questions

All core technology choices are now **permanent, accepted decisions** (see
[../adr/README.md](../adr/README.md)): backend language (ADR-0002), **vector DB = Qdrant
and search = OpenSearch** (ADR-0003), **event backbone = Redpanda/Kafka** (ADR-0004),
serving (ADR-0005), multi-tenancy (ADR-0006), base model family (ADR-0007), agent runtime
(ADR-0008), auth (ADR-0009), MLOps (ADR-0010). These change only if a materially better
technology emerges (via a new/superseding ADR).

**Still open** (not architectural staging — genuinely undecided or empirical):
1. API gateway technology (Envoy vs FastAPI edge) — **REQUIRES DECISION**.
2. Plugin sandbox mechanism (container/WASM/subprocess) — **REQUIRES DECISION** (default
   container isolation pending a spike).
3. Embedding/reranker model choice — **REQUIRES RESEARCH** (tuned via retrieval eval).
4. Monorepo vs polyrepo — recommended monorepo; confirm as ADR-0011 at Phase 01.
5. Training/inference hardware sizing & SLSA target level — **REQUIRES RESEARCH** (measure).

## Related Documents

- [../03-Architecture/SystemArchitecture.md](../03-Architecture/SystemArchitecture.md)
- [./Dependencies.md](./Dependencies.md)
- [../08-AI/InferenceArchitecture.md](../08-AI/InferenceArchitecture.md)
