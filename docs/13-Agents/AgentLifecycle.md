---
title: Agent Lifecycle
document_id: AGT-002
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: AI
audience: AI engineers
phase: Documentation Bootstrap (M000)
related:
  - ./AgentFramework.md
  - ./HumanApproval.md
---

# Agent Lifecycle

> **Purpose.** Define an agent run's states from invocation to completion, including
> approval pauses and failure handling.

## 1. Run States

```mermaid
stateDiagram-v2
    [*] --> Created
    Created --> Planning
    Planning --> AwaitingApproval: consequential action
    AwaitingApproval --> Planning: approved
    AwaitingApproval --> Halted: rejected/timeout
    Planning --> Executing
    Executing --> Planning: observe & continue
    Executing --> Completed: goal met
    Executing --> Failed: error/limit
    Halted --> [*]
    Completed --> [*]
    Failed --> [*]
```

## 2. Run Record

- Each run has a ULID `run_id`; records goal, plan steps, tool calls (inputs/outputs),
  approvals, model calls, and outcome — immutable audit
  ([../10-Security/AgentSecurity.md](../10-Security/AgentSecurity.md)).

## 3. Approval Pauses

- On consequential actions, the run pauses (AwaitingApproval) and resumes on approval or
  halts on rejection/timeout ([./HumanApproval.md](./HumanApproval.md)).

## 4. Limits & Failure

- Step/loop/time/cost limits move a run to Failed with a clear reason; partial results and
  full trace retained.

## 5. Idempotency & Resumability

- Checkpoints enable safe resume; tool calls use idempotency where side-effecting
  ([../12-API/APIStandards.md](../12-API/APIStandards.md)).

## 6. Cleanup

- Ephemeral state cleared post-run per retention; audit retained
  ([../10-Security/DataSecurity.md](../10-Security/DataSecurity.md)).
