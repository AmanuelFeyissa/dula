---
title: Dula Documentation
hide:
  - navigation
  - toc
---

# Dula

**Dula is a cybersecurity AI ecosystem** — a platform for security teams and a
cybersecurity‑specialized AI that assists with the work, deployable anywhere from a laptop to an
air‑gapped cluster.

The name comes from Oromo: *Duulaa* (warrior/knight); *Abbaa Duulaa* (the war leader / defense
commander).

<div class="grid cards" markdown>

-   :material-shield-lock:{ .lg .middle } **Dula Platform**

    ---

    The application, orchestration, integration, security, and operations layer — APIs, LLM
    Gateway, RAG, agents, plugins, automation, multi‑tenancy, audit, and observability.

    [:octicons-arrow-right-24: Core concepts](02-Vision/Vision.md)

-   :material-robot:{ .lg .middle } **Dula AI**

    ---

    The cybersecurity‑specialized intelligence layer — grounded Q&A, CTI extraction, detection
    authoring, triage, and agentic workflows, model‑agnostic behind the LLM Gateway.

    [:octicons-arrow-right-24: Using Dula AI](17-User-Documentation/AskDulaUserGuide.md)

</div>

## Start here

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **Get started**

    ---

    Stand up Dula locally and make your first grounded query in minutes.

    [:octicons-arrow-right-24: Getting started](getting-started.md)

-   :material-account:{ .lg .middle } **For users**

    ---

    Ask Dula, triage alerts, manage incidents and assets, author detections, run the
    investigation agent and playbooks.

    [:octicons-arrow-right-24: Using Dula](17-User-Documentation/README.md)

-   :material-server-network:{ .lg .middle } **For operators**

    ---

    Deploy across local, Docker, Kubernetes, cloud, on‑prem, hybrid, and air‑gapped profiles;
    configure auth, observability, and backup/DR.

    [:octicons-arrow-right-24: Administration](11-Deployment/README.md)

-   :material-code-braces:{ .lg .middle } **For developers**

    ---

    Architecture, API reference, the agent framework, and the plugin/connector SDK.

    [:octicons-arrow-right-24: Developer docs](01-Project/README.md)

</div>

## What Dula helps with

Security operations and SOC work · threat detection and hunting · incident response · threat
intelligence · vulnerability analysis · security log analysis · detection engineering
(Sigma/YARA) · malware‑ and forensics‑analysis assistance · cloud and Kubernetes security ·
security automation and reporting · AI agents and tool integrations.

!!! info "Defensive‑only"
    Dula is a **defensive** security assistant. It refuses operational offensive requests, and
    every model, prompt, RAG, and agent change ships only with measured, non‑regressing quality
    **and** safety. See the [AI threat model](10-Security/AIThreatModel.md).

## Deploy anywhere

From one codebase and chart set: **local · Docker · Kubernetes · cloud · on‑prem · hybrid ·
air‑gapped / offline**. A capability that cannot degrade gracefully offline is not considered
done. See [deployment profiles](11-Deployment/README.md).
