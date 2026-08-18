---
title: Glossary
document_id: PRJ-001
status: Draft
version: 0.1.0
last_updated: 2026-08-18
owner: Engineering
audience: All contributors
phase: Documentation Bootstrap (M000)
---

# Glossary

> **Purpose.** Single source of truth for terminology. If a term is used in the docs, it
> is defined here. Add new terms in the same change that introduces them.

## Product & Ecosystem

- **Dula** — name of the combined ecosystem and of the platform (Product 1). From the
  Oromo language (*Duulaa* = warrior/knight; *Abbaa Duulaa* = war leader / defense
  commander). Decided in ADR-0001 (see [../02-Vision/Vision.md](../02-Vision/Vision.md)).
- **Dula Platform** — Product 1: the enterprise cybersecurity AI platform (APIs, UI,
  RAG, agents, integrations, deployment).
- **Dula AI** — Product 2: the cybersecurity-specialized large language model(s) and the
  training/evaluation/serving stack around them.

## Cybersecurity Domain

- **SOC** — Security Operations Center.
- **SIEM** — Security Information and Event Management.
- **SOAR** — Security Orchestration, Automation and Response.
- **EDR/XDR** — Endpoint / Extended Detection and Response.
- **IR** — Incident Response.
- **CTI** — Cyber Threat Intelligence.
- **IOC / IOA** — Indicator of Compromise / Indicator of Attack.
- **TTP** — Tactics, Techniques, and Procedures.
- **MITRE ATT&CK** — knowledge base of adversary TTPs.
- **CVE / NVD** — Common Vulnerabilities and Exposures / National Vulnerability Database.
- **CVSS** — Common Vulnerability Scoring System; a vector string yields a 0–10 base severity score.
- **KEV** — CISA's Known Exploited Vulnerabilities catalogue (a signal for prioritization).
- **Defang / Refang** — rendering an indicator inert for display (`evil[.]com`, `hxxp://`) /
  reversing that to match the real value.
- **CAPEC** — Common Attack Pattern Enumeration and Classification.
- **Sigma** — generic signature format for SIEM detection rules.
- **YARA** — pattern-matching rules for malware identification.
- **STIX / TAXII** — structured threat-info representation / transport protocol.
- **Detection Engineering** — the discipline of building/maintaining detections.
- **Threat Hunting** — proactive search for undetected threats.
- **Alert** — a detection signal to be triaged; may relate to an asset and escalate to an incident.
- **Incident** — an investigation case aggregating one or more alerts (the IR spine).
- **Asset** — a monitored entity (host, account, cloud/K8s resource).

## AI / ML

- **LLM** — Large Language Model.
- **RAG** — Retrieval-Augmented Generation.
- **Embedding** — vector representation of text used for semantic search.
- **Vector database** — store optimized for nearest-neighbor search over embeddings.
- **Hybrid search** — combination of lexical (BM25) and vector search.
- **Fine-tuning** — adapting a pretrained model to a task/domain.
- **LoRA / QLoRA** — parameter-efficient fine-tuning; QLoRA adds quantization.
- **Quantization** — reducing numeric precision of weights (e.g. INT4) to cut memory.
- **Distillation** — training a smaller model to mimic a larger one.
- **Inference** — running a trained model to produce output.
- **Tool calling** — an LLM invoking defined functions/tools.
- **Agent** — an LLM-driven component that plans and acts via tools under policy.
- **Agent runtime** — the first-party component that executes an agent's plan/act loop and
  enforces permissions, approval, limits, and audit; the planner only *proposes*, the runtime
  decides and executes.
- **Side-effect class** — a tool's classification as **read** (permissioned, no approval) or
  **consequential** (writes/containment; requires human approval).
- **Approval broker** — the human-in-the-loop component that pauses a run for a consequential
  action and resolves it on approve/reject (or timeout → halt).
- **Consequential action** — an irreversible/high-impact tool action (e.g. create a ticket,
  isolate a host) that requires explicit human approval by default.
- **Playbook** — a declarative, multi-step security procedure compiled into a planner and run by
  the agent runtime; read steps run automatically, consequential steps pause for approval. It
  adds no new execution path, so all agent controls (permissions, approval, limits, audit) apply.
- **Approval checkpoint** — the point in a playbook where a consequential step pauses the run for
  human approval before it can execute.
- **Grounded report** — an executive/technical report derived strictly from a run's trace, citing
  the step each statement came from, with tool output labelled untrusted; it never claims an
  action that did not actually execute.
- **Values overlay** — a Helm values file that expresses a deployment profile's differences
  (cloud/on-prem/hybrid/air-gapped) on top of one shared chart; profiles differ by config, not code.
- **Admission control** — cluster-side enforcement (Kyverno, ADR-0015) that admits only pods
  meeting policy: cosign-signed images plus the pod-security baseline (non-root, read-only rootfs,
  dropped caps, resource limits).
- **SBOM** — Software Bill of Materials; the itemized inventory of everything in a build/image,
  generated with syft and attached as a signed attestation.
- **SLSA** — Supply-chain Levels for Software Artifacts; Dula targets **Build Level 3** (hardened,
  non-falsifiable, signed provenance).
- **No-egress assertion** — a CI check that renders the air-gapped profile and fails if it would
  reach outside the enclave (external egress, non-mirror images, or a public endpoint).
- **GA readiness** — the honest checklist separating what Phase 09 delivered/verified from the
  operational items (live deploy, pen test, DR drill) that require real infrastructure.
- **Guardrails** — input/output controls constraining model/agent behavior.
- **LLM Gateway** — internal service abstracting model providers/runtimes.
- **Evaluation / Benchmark** — measuring model/system quality against a fixed dataset.
- **Chunking** — splitting documents into retrievable units with provenance metadata.
- **Reciprocal Rank Fusion (RRF)** — combining ranked result lists (e.g. vector + BM25) by summing 1/(k+rank).
- **Reranking** — reordering retrieved candidates for precision (e.g. cross-encoder or overlap).
- **Grounding / Groundedness** — answering only from retrieved evidence, with citations.
- **Citation** — an evidence reference (`[n]`) attributing a claim to a source chunk.
- **Prompt injection** — direct (user) or indirect (via retrieved/tool content) attempts to override instructions; defended by trust separation.
- **Provider** — a pluggable model backend behind the gateway (extractive, Ollama, vLLM, llama.cpp).
- **SFT (Supervised Fine-Tuning)** — instruction tuning on curated input→output examples.
- **Contamination** — training data overlapping the held-out benchmark; must be zero.
- **Ship/retire gate** — the rule that a tuned candidate may ship only if it beats the baseline and does not regress safety; otherwise it is retired.
- **Model registry** — the record of model versions, variants, metrics, and decisions; artifact naming `dula-<base>-<task>-<method>-vX.Y`.
- **Model card** — a document stating a model's base, data, metrics, decision, intended use, and safety posture.
- **Lifecycle stage** — a registered model version's position in `staging → canary → production →
  superseded/rejected/archived`; every transition is a new, append-only registry entry, never a
  mutation of a past one.
- **Canary deployment** — routing a configurable fraction of live traffic to a candidate model
  alongside production, so its real-world quality/safety/latency can be observed before full
  promotion.
- **Rollback (model)** — re-promoting the most recently superseded version straight back to
  `production`; appending the registry transition is "propose and record" — actually shifting
  live traffic to match is a separate, reviewed redeploy step.
- **Drift detection** — scheduled re-evaluation of whatever is currently `production` against its
  own recorded baseline, to catch quality/safety degradation over time (e.g. from changing
  knowledge indices), independent of any new candidate being trained.

## Platform & Ops

- **Tenant** — an isolated customer/organization within a deployment.
- **Multi-tenancy** — serving multiple tenants from shared infrastructure with isolation.
- **RBAC / ABAC** — Role- / Attribute-Based Access Control.
- **OPA / Rego** — Open Policy Agent and its policy language; externalizes authorization.
- **RLS** — Row-Level Security; Postgres row filtering used for tenant isolation.
- **Event backbone / bus** — Redpanda (Kafka API) stream carrying `domain.entity.action` events.
- **Idempotent consumer** — a worker that safely processes at-least-once delivery by
  deduplicating on event id.
- **Audit event** — an immutable record of data access / authorization decisions.
- **Ports & adapters** — layering that isolates domain logic from infrastructure (repos, bus).
- **Soft delete** — marking a row deleted (`deleted_at`) instead of removing it, for audit/history.
- **Connector** — integration adapter to an external security system.
- **Plugin** — packaged, sandboxed extension providing connectors/tools/capabilities.
- **Plugin manifest** — a plugin's signed declaration: identity, version, capabilities, required
  permissions, egress allowlist, and resource limits; the host grants only what it declares.
- **Capability** — a named connector operation (`<system>.<capability>`, e.g. `siem.search`),
  classified read or consequential.
- **Egress allowlist** — the default-deny set of external hosts a plugin may reach; everything
  else is blocked, with SSRF protection.
- **SSRF** — Server-Side Request Forgery; blocked by refusing requests that resolve to
  private/loopback/link-local addresses.
- **Plugin signing** — Ed25519 signature over the manifest, verified against a trust store before
  install, so tampered or untrusted plugins are rejected (and publishers can be revoked).
- **Deployment profile** — a supported deployment shape: cloud, on-prem, hybrid,
  air-gapped (see [../11-Deployment/README.md](../11-Deployment/README.md)).
- **Air-gapped** — an environment with no external network connectivity.
- **Observability** — logs, metrics, traces used to understand system behavior.
- **SBOM** — Software Bill of Materials.

## Lifecycle & Documentation

- **Technical Documentation** — engineering docs (areas `00`–`16`, `adr/`) for developers,
  architects, security/ML/DevOps engineers, and maintainers: how it works / is built.
- **User Documentation** — user/operator docs (`17-User-Documentation/`) for end users,
  administrators, and operators: how to use / run / operate.
- **Documentation Impact Assessment** — the 11-question review done at each milestone
  (CLAUDE.md §11.6) determining which docs were created/updated/not-applicable.
- **Milestone Closure Report** — required completion document per milestone
  (`04-MVP-Roadmap/closure/M0NN-<slug>-Closure.md`, CLAUDE.md §11.8).
- **Phase Completion Review** — required document when a phase completes
  (`04-MVP-Roadmap/closure/PhaseNN-<slug>-Completion-Review.md`, CLAUDE.md §11.9).
- **DOCUMENTATION-INCOMPLETE** — milestone status when implementation/tests/security are
  done but required documentation is not; blocks `COMPLETE` (CLAUDE.md §11.8).

## Documentation Maturity Tags

- **CURRENT** — true today. **MVP** — targeted for first release. **FUTURE** — later.
- **RESEARCH / EXPERIMENTAL** — under investigation / prototyped.
- **REQUIRES RESEARCH / REQUIRES DECISION** — unresolved question / pending decision.
