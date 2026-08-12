---
title: Phase 06 — Agents
document_id: MVP-006
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: AI / Security
audience: All contributors
phase: Documentation Bootstrap (M000)
related:
  - ../03-Architecture/AgentArchitecture.md
  - ../13-Agents/README.md
---

# Phase 06 — Agents

> **Purpose.** Introduce safe AI agents that plan and act with permissioned tools and
> human approval — only after safety controls are proven.

## Objective
Deliver the agent runtime with tool calling, permissions, human approval, and audit;
enable investigation/timeline assistance (UC-03) as the first agentic use case.

## Scope
- Agent runtime ([../13-Agents/AgentFramework.md](../13-Agents/AgentFramework.md)); build
  vs LangGraph decided (ADR-0008).
- Tool calling + permission model + approval broker
  ([../13-Agents/ToolCalling.md](../13-Agents/ToolCalling.md),
  [../13-Agents/AgentPermissions.md](../13-Agents/AgentPermissions.md),
  [../13-Agents/HumanApproval.md](../13-Agents/HumanApproval.md)).
- Read-only internal tools first (search logs, enrich); consequential actions gated.

## Dependencies
- Phases 03–05; RAG + Dula AI available; core services provide tools.

## Deliverables
- An agent that assists an investigation end-to-end using read-only tools, with full audit
  and approval gating for any consequential step.

## Implementation Requirements
- Step/loop/time/cost limits; isolated execution; untrusted tool output handling
  ([../10-Security/AgentSecurity.md](../10-Security/AgentSecurity.md)).

## Tests
- **Agent evaluation** (task success + safety); adversarial: no escalation / no
  unauthorized action under injection ([../15-Testing/AgentEvaluation.md](../15-Testing/AgentEvaluation.md)).

## Security Requirements
- Agent ⊆ user permissions; approval for consequential actions; complete audit trail.

## Documentation
- Agent definitions, tool catalog, approval policy; update PROJECT_STATE; ADR-0008.

## Acceptance Criteria
- Agent completes the investigation scenario; safety suite passes with **zero** unauthorized
  actions; every consequential step required approval.

## Definition of Done
- Global DoD + above; safety failures are blocking.
