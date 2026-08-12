---
title: Glossary
document_id: PRJ-001
status: Draft
version: 0.1.0
last_updated: 2026-08-11
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
- **CAPEC** — Common Attack Pattern Enumeration and Classification.
- **Sigma** — generic signature format for SIEM detection rules.
- **YARA** — pattern-matching rules for malware identification.
- **STIX / TAXII** — structured threat-info representation / transport protocol.
- **Detection Engineering** — the discipline of building/maintaining detections.
- **Threat Hunting** — proactive search for undetected threats.

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
- **Guardrails** — input/output controls constraining model/agent behavior.
- **LLM Gateway** — internal service abstracting model providers/runtimes.
- **Evaluation / Benchmark** — measuring model/system quality against a fixed dataset.

## Platform & Ops

- **Tenant** — an isolated customer/organization within a deployment.
- **Multi-tenancy** — serving multiple tenants from shared infrastructure with isolation.
- **RBAC / ABAC** — Role- / Attribute-Based Access Control.
- **Connector** — integration adapter to an external security system.
- **Plugin** — packaged, sandboxed extension providing connectors/tools/capabilities.
- **Deployment profile** — a supported deployment shape: cloud, on-prem, hybrid,
  air-gapped (see [../11-Deployment/README.md](../11-Deployment/README.md)).
- **Air-gapped** — an environment with no external network connectivity.
- **Observability** — logs, metrics, traces used to understand system behavior.
- **SBOM** — Software Bill of Materials.

## Documentation Maturity Tags

- **CURRENT** — true today. **MVP** — targeted for first release. **FUTURE** — later.
- **RESEARCH / EXPERIMENTAL** — under investigation / prototyped.
- **REQUIRES RESEARCH / REQUIRES DECISION** — unresolved question / pending decision.
