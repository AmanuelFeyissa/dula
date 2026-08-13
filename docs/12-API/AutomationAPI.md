---
title: Automation API (Playbooks, Runs, Reports)
document_id: API-007
status: Draft
version: 0.1.0
last_updated: 2026-08-13
owner: AI / Backend
audience: Developer, API consumer
phase: Phase 08 — Automation (M008)
related:
  - ./Authentication.md
  - ./Authorization.md
  - ./AgentsAPI.md
  - ./AIGatewayAPI.md
  - ../13-Agents/Playbooks.md
  - ../17-User-Documentation/PlaybooksUserGuide.md
---

# Automation API

> **Purpose.** HTTP surface for security automation on the AI Gateway (`apps/ai-gateway`). List
> playbooks, run one, read its trace, approve/reject a paused consequential step, and fetch a
> grounded report. Design and guarantees: [../13-Agents/Playbooks.md](../13-Agents/Playbooks.md).
> **Status: CURRENT** (offline profile).

All endpoints require a valid bearer token ([Authentication.md](./Authentication.md)) and are
authorized per-action via OPA ([Authorization.md](./Authorization.md)); requests are tenant-scoped
and a run/report is **never** returned to a tenant that does not own it.

A playbook run **is** an agent run — consequential steps pause at `awaiting_approval` and the
runtime enforces every control ([AgentsAPI.md](./AgentsAPI.md)). The per-tool permissions
(`tool.list_alerts`, `tool.enrich_indicator`, `tool.search_logs`, `tool.create_ticket`) are
enforced by the runtime at each step in addition to the endpoint action below.

## Endpoints

| Method & path | OPA action | Description |
|---------------|-----------|-------------|
| `GET /api/v1/automation/playbooks` | `automation.read` | List available playbooks + their steps |
| `POST /api/v1/automation/playbooks/{name}/runs` | `automation.run` | Start a playbook run (optional `goal`) |
| `GET /api/v1/automation/runs/{run_id}` | `automation.read` | Read a run's trace/state |
| `POST /api/v1/automation/runs/{run_id}/approval` | `automation.approve` | Approve/reject a paused action |
| `GET /api/v1/automation/runs/{run_id}/report` | `reports.read` | Grounded executive + technical report |

## Run a playbook

```http
POST /api/v1/automation/playbooks/triage-enrich-ticket/runs
Authorization: Bearer <token>
Content-Type: application/json

{ "goal": "Investigate the outbound beacon" }
```

Response (`200`) — the run paused at the consequential ticket step:

```json
{
  "run_id": "0c1f…",
  "playbook": "triage-enrich-ticket",
  "goal": "Investigate the outbound beacon",
  "state": "awaiting_approval",
  "result": null,
  "error": null,
  "steps": [
    {"index": 0, "tool": "list_alerts", "side_effect": "read", "permitted": true, "approved": null, "executed_ok": true},
    {"index": 1, "tool": "enrich_indicator", "side_effect": "read", "permitted": true, "approved": null, "executed_ok": true},
    {"index": 2, "tool": "search_logs", "side_effect": "read", "permitted": true, "approved": null, "executed_ok": true},
    {"index": 3, "tool": "create_ticket", "side_effect": "consequential", "permitted": true, "approved": null, "executed_ok": null}
  ],
  "pending_approval": {"step": 3, "tool": "create_ticket", "args": {"title": "Investigation: …"}, "impact": "Creates an incident ticket: …"}
}
```

## Approve the paused action

```http
POST /api/v1/automation/runs/0c1f…/approval
{ "approved": true }
```

The run resumes as the **original invoker** (never the approver's authority) and completes; a
`false` decision **halts** it with no ticket created. Approving a run that is not
`awaiting_approval` returns `409`.

## Fetch the report

```http
GET /api/v1/automation/runs/0c1f…/report
```

Response (`200`):

```json
{
  "run_id": "0c1f…",
  "title": "Incident report — Investigate the outbound beacon",
  "state": "completed",
  "outcome": "Playbook completed.",
  "executive_summary": "An automated investigation … Consequential actions: `create_ticket` (approved by lead) → TICKET-1. Playbook completed.",
  "technical_detail": "| # | Step | Permitted | Approval | Result | …",
  "evidence": [
    {"ref": "step[0]:list_alerts", "kind": "alert", "summary": "Suspicious outbound beacon on HOST-7", "untrusted": true},
    {"ref": "step[3]:create_ticket", "kind": "ticket", "summary": "Created ticket TICKET-1", "untrusted": true}
  ],
  "markdown": "# Incident report — …"
}
```

## Errors

| Status | When |
|--------|------|
| `401` | Missing/invalid token |
| `403` | Caller not authorized for the endpoint action |
| `404` | Unknown playbook, or run not found / owned by another tenant |
| `409` | Approving a run that is not awaiting approval |

## Notes

- Reports are **grounded** strictly in the run trace and label tool output as **untrusted**
  evidence; a rejected/halted run never claims a ticket was created.
- Consequential connectors are still reached only via a run's approval gate — there is no
  auto-approval path (see [../13-Agents/Playbooks.md](../13-Agents/Playbooks.md)).
