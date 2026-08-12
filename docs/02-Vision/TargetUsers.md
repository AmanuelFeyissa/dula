---
title: Target Users & Personas
document_id: VIS-003
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Product
audience: Product, design, engineering
phase: Documentation Bootstrap (M000)
related:
  - ./UseCases.md
  - ./Vision.md
---

# Target Users & Personas

> **Purpose.** Define who Dula serves so features and priorities can be traced to real
> user needs.

## 1. Primary Segments

- **Enterprise security teams** (SOC, IR, threat intel, detection engineering).
- **MSSPs** (multi-tenant service providers) — drives multi-tenancy requirements.
- **Government / regulated / defense** — drives air-gapped and data-sovereignty needs.
- **Security researchers & red/blue teams** (authorized) — drive analysis assistance.

## 2. Personas

### 2.1 Tier-1 SOC Analyst — "Maya"
- **Goals:** triage alerts fast, reduce false positives, know what to do next.
- **Pains:** alert fatigue, context-switching across tools, shallow enrichment.
- **Dula value:** grounded triage summaries, enrichment, suggested next steps with
  citations. (Use cases: [UseCases.md](./UseCases.md) UC-01, UC-06.)

### 2.2 Threat Hunter / Tier-3 Analyst — "Dev"
- **Goals:** form and test hypotheses, pivot across telemetry, map to ATT&CK.
- **Pains:** query-language friction, correlating disparate sources.
- **Dula value:** natural-language hunting, ATT&CK-mapped guidance, query generation
  reviewed before execution. (UC-02, UC-07.)

### 2.3 Incident Responder — "Priya"
- **Goals:** scope incidents, build timelines, produce reports.
- **Pains:** manual timeline reconstruction, reporting overhead.
- **Dula value:** investigation assistance, timeline drafting, report generation with
  evidence links. (UC-03, UC-09.)

### 2.4 Detection Engineer — "Sam"
- **Goals:** write/tune Sigma/YARA and detections, reduce noise.
- **Pains:** rule authoring, coverage gaps vs ATT&CK.
- **Dula value:** detection drafting, coverage analysis, test-case generation. (UC-04.)

### 2.5 CTI Analyst — "Lin"
- **Goals:** track actors/campaigns, operationalize intel (STIX/TAXII).
- **Dula value:** summarize advisories, extract IOCs/TTPs, correlate to internal data.
  (UC-05.)

### 2.6 Security Engineer / Platform Owner — "Omar"
- **Goals:** deploy, secure, integrate, and operate Dula (incl. air-gapped).
- **Dula value:** portable deployment, integrations, observability, RBAC. (UC-08, UC-10.)

### 2.7 CISO / Security Leadership — "Grace"
- **Goals:** risk posture, metrics, governance, compliance.
- **Dula value:** reporting/dashboards, auditability, data-sovereignty guarantees.

## 3. Anti-Personas (Not Served)

- Attackers seeking exploit generation or attack automation.
- Users seeking a general-purpose consumer assistant.

## 4. Access & Roles

Personas map to RBAC roles enforced by the platform (see
[../12-API/Authorization.md](../12-API/Authorization.md)); consequential agent actions
require human approval regardless of role
([../13-Agents/HumanApproval.md](../13-Agents/HumanApproval.md)).
