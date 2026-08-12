---
title: Vision
document_id: VIS-001
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Product / Founding Engineering
audience: All stakeholders
phase: Documentation Bootstrap (M000)
related:
  - ./ProductStrategy.md
  - ./TargetUsers.md
  - ../04-MVP-Roadmap/MVPOverview.md
---

# Vision

> **Purpose.** State what we are building, why, for whom, and — just as importantly —
> what we are *not* building. Capabilities are labeled by maturity to avoid overstating
> what exists today (nothing is implemented yet).

## 1. Mission

Give security teams a trustworthy AI ecosystem that measurably reduces the time to
detect, understand, and respond to threats — deployable anywhere their data must live,
including fully **air-gapped** environments — without sending sensitive security data to
third parties.

## 2. Vision Statement

A production-grade cybersecurity AI ecosystem — not a chatbot — combining:

- **Dula Platform (Product 1):** an enterprise platform delivering SOC assistance,
  threat detection/hunting, incident response, threat intelligence, vulnerability and
  malware-analysis assistance, log analysis, detection engineering, forensics assistance,
  cloud/Kubernetes security, automation, reporting, investigation, knowledge management,
  AI agents, and security-tool integrations.
- **Dula AI (Product 2):** cybersecurity-specialized language model(s) and the
  training/evaluation/serving stack behind them, tuned for security reasoning and
  designed to run locally/offline.

Both are **independently deployable** yet integrate through shared contracts.

## 3. Product Naming

**DECIDED (ADR-0001, Accepted).** The names are:

- **Dula** — the Cybersecurity AI Platform (Product 1); also the name of the overall
  ecosystem. "Dula Platform" refers specifically to Product 1 when disambiguation is
  needed.
- **Dula AI** — the cybersecurity-specialized large language model(s) (Product 2).

**Etymology.** *Dula* derives from the Oromo language: **Duulaa** means *a warrior or
knight*; **Abbaa Duulaa** is the traditional war leader, army commander, or defense
minister within the Gadaa system. The name reflects the product's defensive mission —
a guardian and commander of the defense — consistent with the defensive-only principle in
[GuidingPrinciples.md](./GuidingPrinciples.md).

> **Trademark clearance** remains a business task before external/commercial use, but the
> engineering names are now fixed and used consistently across all documentation. See
> [ADR-0001](../adr/ADR-0001-product-naming.md).

## 4. What Success Looks Like

- Security analysts complete triage, hunts, and investigations faster and with better
  grounding, with AI outputs that cite evidence.
- The platform runs in cloud, on-prem, hybrid, and air-gapped modes from the same
  codebase and charts.
- Dula AI demonstrably outperforms comparable general models on a **published internal
  cybersecurity benchmark** (see [../08-AI/Benchmarking.md](../08-AI/Benchmarking.md)).
- AI actions are safe by construction: permissioned tools, human approval for
  consequential actions, and full auditability.

## 5. Capability Maturity (Honest Baseline)

| Capability area | Maturity today |
|-----------------|----------------|
| Any running software | **None** — Documentation Bootstrap only |
| Core platform (API/UI/auth) | **MVP** target (Phases 01–02) |
| RAG over security knowledge | **MVP** (Phase 03) |
| Dula AI (base model + tuning) | **MVP → FUTURE** (Phase 04+) |
| Agents & automation | **FUTURE** (Phases 06, 08) |
| Integrations/plugins | **FUTURE** (Phase 07) |
| Advanced training / pretraining | **RESEARCH** (Phase 11) |

## 6. Non-Goals (Bootstrap-Level)

See [ProductStrategy.md](./ProductStrategy.md) §Non-Goals for the full list. In brief, we
are **not** building an offensive/attack-automation product, **not** training a
foundation model from scratch initially, and **not** a generic chatbot.

## 7. Long-Term Direction

Progress from retrieval-grounded assistance → specialized fine-tuned models → safe
autonomous-but-supervised agents → an extensible security-AI platform ecosystem, always
preserving self-hostable and air-gapped operation. Detailed staging lives in
[../08-AI/AIResearchRoadmap.md](../08-AI/AIResearchRoadmap.md) and
[../03-Architecture/ArchitectureRoadmap.md](../03-Architecture/ArchitectureRoadmap.md).

## Related Documents

- [./ProductStrategy.md](./ProductStrategy.md) · [./TargetUsers.md](./TargetUsers.md) ·
  [./UseCases.md](./UseCases.md) · [./GuidingPrinciples.md](./GuidingPrinciples.md)
