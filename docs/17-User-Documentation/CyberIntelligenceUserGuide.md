---
title: Cyber Intelligence — User Guide (CTI, Vulnerabilities, Detections)
document_id: USR-003
status: Draft
version: 0.1.0
last_updated: 2026-08-13
owner: Product / Docs
audience: End User, Operator, Security Engineer
phase: Phase 05 — Cyber Intelligence (M005)
related:
  - ./README.md
  - ./AskDulaUserGuide.md
  - ../12-API/AIGatewayAPI.md
  - ../08-AI/CyberIntelligence.md
---

# Cyber Intelligence — User Guide

> **Purpose.** How to use Dula's cyber-intelligence features: extract indicators and TTPs from
> a threat advisory, prioritize a vulnerability, and draft detection rules. **Status: MVP.**
> Technical reference: [../08-AI/CyberIntelligence.md](../08-AI/CyberIntelligence.md).

## What it does

- **CTI extraction** — paste a threat advisory; Dula pulls out the indicators of compromise
  (IPs, domains, URLs, hashes, CVEs), maps the attacker techniques to **MITRE ATT&CK**, and
  produces a shareable **STIX 2.1** bundle — plus an optional plain-language summary.
- **Vulnerability analysis** — give a CVSS vector and a little context (is it being exploited?
  is the asset internet-facing?) and Dula returns a **severity, a P1–P4 priority, and the
  reasons** behind that priority.
- **Detection authoring** — from the same advisory, Dula drafts a **Sigma** or **YARA** rule
  and checks that it is syntactically valid before handing it to you. It can also validate a
  rule you wrote or an AI drafted elsewhere, and show your detection **coverage against ATT&CK**.

Everything runs **offline** and treats the advisory as untrusted: extracted indicators are
shown **defanged** (e.g. `evil[.]com`) so you never click them by accident, and Dula will not
help with offensive/attack tooling.

## Using the Intel workbench

1. Sign in and open **Intel** in the top navigation.
2. Choose a tab — **CTI Extract**, **Vulnerability**, or **Detections** — paste an advisory or
   CVSS vector, and submit.
3. Results (indicators, techniques, STIX bundle, priority + rationale, or a rule with its
   validation status) render below the form.

The sections below describe the same capabilities via the API, for automation or integration.

## Extract intelligence from an advisory

Send the advisory text to `POST /api/v1/intel/extract`:

```json
{ "advisory": "The actor sent spearphishing emails; the loader beacons to hxxp://bad[.]example[.]com and 198.51.100.23. See CVE-2024-9999.", "summarize": true }
```

You get back the `indicators` (defanged), the ATT&CK `techniques`, a `stix_bundle` you can
import into a TIP, and a `summary`. If an advisory tries to hide instructions to the AI
("ignore previous instructions…"), Dula flags it and does not obey it.

## Prioritize a vulnerability

Send a CVSS vector and context to `POST /api/v1/intel/vulnerability`:

```json
{ "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H", "known_exploited": true, "internet_facing": true, "asset_criticality": "high" }
```

You get the CVSS `base_score`, a `severity`, a `priority` (P1–P4), a `risk_score`, and a
`rationale` list explaining every factor — so you can defend the decision in a change review.
A critical, actively-exploited, internet-facing vulnerability comes back **P1**.

## Draft a detection rule

Send an advisory to `POST /api/v1/intel/detections/sigma` (or `.../yara`):

```json
{ "title": "Evil C2 beacon", "advisory": "Malware beacons to evil[.]example[.]com over HTTP.", "category": "proxy", "attack_tags": ["attack.t1071"] }
```

You get a ready-to-review `rule`, plus `valid`, `errors`, and `warnings`. Dula only returns
rules that pass validation. To check a rule you already have, use
`POST /api/v1/intel/detections/validate` with `{"format": "sigma"|"yara", "rule": "..."}`.

## Check ATT&CK coverage

Send your rules' tags to `POST /api/v1/intel/detections/coverage` to see which techniques and
tactics you cover, which are **gaps**, and a coverage ratio against a target technique list.

## Good to know

- You need to be signed in, and your role must permit the action; every request is
  tenant-scoped and audited.
- Extraction and rule generation are deterministic — the same advisory always gives the same
  result, which makes intel reviewable and repeatable.
- The ATT&CK catalog and extractors are curated (not exhaustive) today; review Dula's output
  before operational use, as you would any analyst draft.

## Getting help

- API reference: [../12-API/AIGatewayAPI.md](../12-API/AIGatewayAPI.md).
- Grounded Q&A / triage: [./AskDulaUserGuide.md](./AskDulaUserGuide.md).
