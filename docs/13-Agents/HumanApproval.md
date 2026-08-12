---
title: Human Approval
document_id: AGT-005
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Security / AI / Product
audience: Security, AI, product
phase: Documentation Bootstrap (M000)
related:
  - ./AgentLifecycle.md
  - ./ToolCalling.md
  - ../02-Vision/GuidingPrinciples.md
---

# Human Approval (Human-in-the-Loop)

> **Purpose.** Define when and how humans approve agent actions — a core safety control
> ([../02-Vision/GuidingPrinciples.md](../02-Vision/GuidingPrinciples.md) §4).

## 1. When Approval Is Required

- Any **consequential/irreversible** action: writes to external systems, containment
  (isolate host, disable account), destructive changes, or anything policy marks
  high-impact. Configurable per tenant/agent, but **default = require approval**.

## 2. Approval Request Content

- The plan/rationale, the **exact** action and parameters, predicted impact, affected
  assets, and the tool's side-effect class — enough for an informed decision.

## 3. Flow

```mermaid
sequenceDiagram
    participant Agent
    participant Broker as Approval Broker
    participant Human
    Agent->>Broker: request approval(action, impact)
    Broker->>Human: present request
    Human-->>Broker: approve / reject
    Broker-->>Agent: decision (or timeout → halt)
```

- Run pauses (AwaitingApproval) and resumes on approve, halts on reject/timeout
  ([./AgentLifecycle.md](./AgentLifecycle.md)).

## 4. Authorization of Approvers

- Only users authorized for the action may approve it (no approving beyond your own
  permissions) ([./AgentPermissions.md](./AgentPermissions.md)).

## 5. Audit

- The request, decision, approver identity, and timestamp are recorded immutably.

## 6. Anti-Fatigue

- Batch/group related low-risk approvals thoughtfully; never auto-approve consequential
  actions; make impact clear to avoid rubber-stamping.
