---
title: Guiding Principles
document_id: VIS-005
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Product / Engineering leadership
audience: All contributors
phase: Documentation Bootstrap (M000)
related:
  - ./Vision.md
  - ../10-Security/README.md
  - ../00-Governance/AIContributionGuidelines.md
---

# Guiding Principles

> **Purpose.** The durable principles that resolve trade-offs when documents or people
> disagree. When in doubt, decide in favor of the higher principle.

## 1. Defensive, Ethical, Lawful

Dula exists to **defend**. We support authorized security testing, defensive operations,
CTF/education, and research. We do **not** build exploit generation, attack automation,
mass-targeting, or malicious evasion capabilities. Dual-use assistance is provided only
with legitimate context. This principle overrides feature requests.

## 2. Data Sovereignty & Privacy

Customer security data is among the most sensitive data that exists. It must be able to
stay entirely within the customer boundary — including fully offline/air-gapped. No core
capability may require sending customer data to an external service.

## 3. Trustworthy AI: Grounded, Cited, Auditable

AI output must be grounded in evidence and cite it. Every consequential AI action is
logged and attributable. We measure quality with benchmarks and do not ship models/agents
that we cannot evaluate.

## 4. Human-in-Command for Consequential Actions

Agents may propose and (where explicitly permitted) perform actions, but consequential or
irreversible actions require human approval by default
([../13-Agents/HumanApproval.md](../13-Agents/HumanApproval.md)). Least privilege applies
to every tool and connector.

## 5. Security by Design

Threat-model first; treat all model output and retrieved content as untrusted; enforce
authZ at the service layer; sandbox plugins/agents; secure the supply chain. See
[../10-Security/README.md](../10-Security/README.md).

## 6. Deploy Anywhere, Same Code

Cloud, on-prem, hybrid, and air-gapped are first-class from one codebase and chart set.
A feature that cannot work offline is not "done" until it degrades gracefully offline.

## 7. Honesty About Maturity

We label capabilities CURRENT / MVP / FUTURE / RESEARCH and never overstate. Unverified
facts are marked **REQUIRES RESEARCH**, never asserted (see
[../00-Governance/AIContributionGuidelines.md](../00-Governance/AIContributionGuidelines.md)).

## 8. Incremental, Evidence-Driven Delivery

Build the smallest useful thing, measure, then expand. The roadmap is staged so each
phase delivers verifiable value and de-risks the next.

## 9. Open, Portable, Minimal

Favor open standards and permissively licensed, self-hostable components; minimize
dependencies and operational surface (see [../01-Project/TechnologyStack.md](../01-Project/TechnologyStack.md)).

## 10. Reproducibility

Datasets, models, experiments, and builds are versioned and reproducible
([../09-MLOps/README.md](../09-MLOps/README.md)).
