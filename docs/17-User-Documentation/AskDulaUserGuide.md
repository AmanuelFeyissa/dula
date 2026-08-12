---
title: Ask Dula — Grounded Q&A and Triage User Guide
document_id: USR-002
status: Draft
version: 0.1.0
last_updated: 2026-08-12
owner: Product / Docs
audience: End User, Operator
phase: Phase 03 — Knowledge & RAG (M003)
related:
  - ./README.md
  - ../12-API/AIGatewayAPI.md
  - ./CoreEntitiesUserGuide.md
---

# Ask Dula — Grounded Q&A and Triage

> **Purpose.** How to use Dula's assistant to get **grounded, cited** answers to security
> questions and to **triage alerts**. **Status: MVP** (first usable AI capability, powered by
> a general model). Technical reference:
> [../12-API/AIGatewayAPI.md](../12-API/AIGatewayAPI.md).

## What it does

Dula answers security questions and triages alerts using **only** the knowledge it can
retrieve — public security knowledge (ATT&CK, CVEs, CISA guidance) plus your tenant's own
documents. Every answer **cites its evidence**, and if Dula cannot find supporting evidence
it tells you rather than guessing.

## Ask a question

1. Sign in and open **Ask** in the top navigation.
2. Keep **Question** selected, type your question (e.g. *"How do I defend against brute force
   attacks?"*), and select **Ask**.
3. The answer streams in, followed by an **Evidence** list — each `[n]` in the answer maps to
   a cited source you can read.

If the answer is marked **(ungrounded)**, Dula did not find supporting evidence; treat it as
"no reliable answer" rather than fact.

## Triage an alert

1. On the **Ask** page choose **Triage alert**.
2. Enter the alert **title**, **severity**, and optional **details**, then select **Ask**.
3. Dula returns a grounded triage — likely meaning, severity rationale, and next steps — with
   citations.

## Add your own knowledge

Administrators/engineers (and analysts) can add tenant-private documents so answers reflect
your environment (runbooks, asset notes). This is done via the API today:

```bash
curl -sX POST http://localhost:8100/api/v1/knowledge/documents \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"text":"Our honeypot is host HP-7.","source":"runbook"}'
```

Your documents are **private to your tenant** — other tenants can never retrieve them.

## Trust & safety

- Answers are **grounded and cited**; verify important decisions against the cited sources.
- Retrieved documents are treated as untrusted data — instructions hidden inside a document
  are ignored, not obeyed (prompt-injection defense).
- Dula assists **defensive** security only and declines operational offensive requests.

## Troubleshooting

- **"Sign in required"** — your session expired; sign in again.
- **429 / "token budget"** — your tenant hit its usage budget; contact an administrator.
- **Ungrounded answers** — add relevant knowledge (above) or rephrase; Dula only answers from
  evidence.
