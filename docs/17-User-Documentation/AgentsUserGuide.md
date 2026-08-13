---
title: Investigation Agent — User Guide
document_id: USR-004
status: Draft
version: 0.1.0
last_updated: 2026-08-13
owner: Product / Docs
audience: End User, Operator, Security Engineer
phase: Phase 06 — Agents (M006)
related:
  - ./README.md
  - ./AskDulaUserGuide.md
  - ../12-API/AgentsAPI.md
  - ../13-Agents/AgentImplementation.md
---

# Investigation Agent — User Guide

> **Purpose.** How to run Dula's investigation agent and approve its actions safely.
> **Status: MVP.** Technical reference:
> [../13-Agents/AgentImplementation.md](../13-Agents/AgentImplementation.md).

## What it does

The investigation agent works a security alert for you: it reviews open alerts, enriches the
indicators (IOCs and ATT&CK techniques), corroborates against logs, and then **recommends** an
incident ticket. It uses **read-only tools on its own**; anything **consequential** (like
creating a ticket, or — for higher-privileged agents — isolating a host) **pauses and waits for
your approval**. You always stay in command.

Key safety properties, enforced by the platform (not the AI):

- The agent can only do what **you** are allowed to do (it inherits a subset of your
  permissions) — it can never escalate.
- Every consequential action needs **explicit human approval**; you see the exact action and its
  impact before deciding.
- Runs are bounded (step/time limits) and every step is **audited**.

## Using the agent

1. Sign in and open **Agents** in the top navigation.
2. Enter (or keep) an investigation **goal** and select **Start investigation**.
3. The agent runs its read-only steps and shows the **trace** — each tool it used and the result.
4. If it recommends a consequential action, the run shows **Approval required** with the impact.
   Choose **Approve** (the action runs and the investigation continues) or **Reject** (the run
   halts and nothing is done).

## Using the API

```json
POST /api/v1/agents/runs
{ "agent": "investigation-assistant", "goal": "Investigate the outbound beacon alert" }
```

The response includes the run `state`, the `steps` taken, and — if paused — a `pending_approval`
describing the action. Approve or reject it:

```json
POST /api/v1/agents/runs/{run_id}/approval
{ "approved": true }
```

Read a run any time with `GET /api/v1/agents/runs/{run_id}`. Full contract:
[../12-API/AgentsAPI.md](../12-API/AgentsAPI.md).

## Good to know

- **Approvals respect your permissions.** You can only approve an action you are yourself
  authorized to perform; otherwise the run halts rather than acting.
- **Tenant-scoped.** You only ever see your own tenant's runs.
- **Reviewable.** The agent's plan is deterministic and every step is recorded — treat its
  output as an analyst draft and confirm important actions.

## Getting help

- API reference: [../12-API/AgentsAPI.md](../12-API/AgentsAPI.md).
- Grounded Q&A / triage: [./AskDulaUserGuide.md](./AskDulaUserGuide.md).
- Cyber intelligence: [./CyberIntelligenceUserGuide.md](./CyberIntelligenceUserGuide.md).
