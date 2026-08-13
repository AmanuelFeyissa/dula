---
title: Agents API (Investigation Runs, Approvals)
document_id: API-006
status: Draft
version: 0.1.0
last_updated: 2026-08-13
owner: AI / Backend
audience: Developer, API consumer
phase: Phase 06 — Agents (M006)
related:
  - ./Authentication.md
  - ./Authorization.md
  - ./AIGatewayAPI.md
  - ../13-Agents/AgentImplementation.md
  - ../03-Architecture/AgentArchitecture.md
  - ../17-User-Documentation/AgentsUserGuide.md
---

# Agents API

> **Purpose.** HTTP surface for AI agents on the AI Gateway (`apps/ai-gateway`). Start an
> investigation run, read its trace, and approve/reject a paused consequential action. Design
> and guarantees: [../13-Agents/AgentImplementation.md](../13-Agents/AgentImplementation.md).
> **Status: CURRENT** (offline profile).

All endpoints require a valid bearer token ([Authentication.md](./Authentication.md)) and are
authorized per-action via OPA ([Authorization.md](./Authorization.md)); requests are
tenant-scoped and a run is **never** returned to a tenant that does not own it.

## Endpoints

| Method & path | OPA action | Description |
|---------------|-----------|-------------|
| `POST /api/v1/agents/runs` | `agents.run` | Start an agent run (`agent`, `goal`) |
| `GET /api/v1/agents/runs/{run_id}` | `agents.read` | Read a run's trace/state |
| `POST /api/v1/agents/runs/{run_id}/approval` | `agents.approve` | Approve/reject a paused action |

Per-tool authorization is additionally enforced by the runtime at each step
(`tool.search_logs`, `tool.enrich_indicator`, `tool.list_alerts`, `tool.create_ticket`,
`tool.isolate_host`) — see the policy mapping in
[../13-Agents/AgentImplementation.md](../13-Agents/AgentImplementation.md).

## Start a run

```json
POST /api/v1/agents/runs
{ "agent": "investigation-assistant", "goal": "Investigate the outbound beacon alert" }
```

Runs synchronously until the agent finishes or **pauses for approval**. Response (`RunOut`):

```json
{
  "run_id": "…", "agent": "investigation-assistant", "goal": "…",
  "state": "awaiting_approval",
  "result": null, "error": null,
  "steps": [
    {"index": 0, "tool": "list_alerts", "side_effect": "read", "permitted": true,
     "approved": null, "executed_ok": true, "thought": "…", "permission_reason": "…"}
  ],
  "pending_approval": {"step": 3, "tool": "create_ticket", "args": {"title": "…"},
                        "impact": "Creates an incident ticket: …"}
}
```

- `state` ∈ `planning | awaiting_approval | executing | completed | failed | halted`.
- Unknown `agent` → **404**. Endpoint authZ failure → **403**.

## Read a run

```json
GET /api/v1/agents/runs/{run_id}   →  RunOut  (404 if not found / not your tenant)
```

## Approve or reject

```json
POST /api/v1/agents/runs/{run_id}/approval
{ "approved": true, "reason": "warranted" }
```

- Resolves the paused action: **approve** re-checks the approver's authorization for that tool,
  executes it, and continues the run; **reject** halts it. Returns the updated `RunOut`.
- Run not awaiting approval → **409**. Approver not authorized for the tool → the run **halts**
  (recorded in `error`), never executes.

## Safety guarantees

The model/planner never executes anything; every step is permission-checked (agent ⊆ user),
consequential steps require human approval, runs are step/cost/time bounded, and the full trace
is audited. See [../13-Agents/AgentImplementation.md](../13-Agents/AgentImplementation.md) and
[../10-Security/AgentSecurity.md](../10-Security/AgentSecurity.md).
