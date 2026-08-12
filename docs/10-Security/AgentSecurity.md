---
title: Agent Security
document_id: SEC-004
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Security / AI
audience: Security, AI engineers
phase: Documentation Bootstrap (M000)
related:
  - ../03-Architecture/AgentArchitecture.md
  - ../13-Agents/AgentPermissions.md
  - ./AIThreatModel.md
---

# Agent Security

> **Purpose.** Define the controls that keep AI agents safe: permissions, isolation,
> approval, limits, and audit. Complements [AIThreatModel.md](./AIThreatModel.md)
> (T7/T8/T11).

## 1. Core Rules

1. **No privilege escalation:** an agent's permissions are a subset of the invoking
   user's; it can never do what the user cannot.
2. **Permissioned tools only:** every tool call passes an OPA authZ check
   ([../13-Agents/AgentPermissions.md](../13-Agents/AgentPermissions.md)).
3. **Human approval** for consequential/irreversible actions by default
   ([../13-Agents/HumanApproval.md](../13-Agents/HumanApproval.md)).
4. **Isolation:** tool execution is sandboxed; side effects constrained by connector
   sandboxing ([./PluginSecurity.md](./PluginSecurity.md)).
5. **Limits:** step/loop/time/cost caps prevent runaway/excessive agency.
6. **Untrusted I/O:** tool outputs and model plans are untrusted; validate before acting.
7. **Full audit:** plan, tools, inputs, outputs, approvals — recorded and replayable.

## 2. Control Flow

See the runtime diagram in
[../03-Architecture/AgentArchitecture.md](../03-Architecture/AgentArchitecture.md): every
step is permission-checked and consequential actions gate on approval.

## 3. Isolation Details

- Agents run in constrained execution contexts; no direct filesystem/network beyond
  declared tools; default-deny egress; scoped credentials injected per tool.

## 4. Anti-Abuse

- Guard against prompt-injection-driven tool abuse (T7): tools require explicit
  authorization independent of what the model "decides"; the model cannot self-grant.

## 5. Evaluation

- Agents are safety-evaluated (no unauthorized actions under adversarial prompts) before
  release ([../15-Testing/AgentEvaluation.md](../15-Testing/AgentEvaluation.md)).

## 6. Incident Handling

- Suspicious agent behavior triggers halt + alert + audit review
  ([../16-Operations/IncidentManagement.md](../16-Operations/IncidentManagement.md)).
