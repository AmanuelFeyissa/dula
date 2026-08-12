---
title: Agents — Overview
document_id: AGT-000
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: AI / Security
audience: AI & security engineers
phase: Documentation Bootstrap (M000)
---

# 13 — Agents

> **Purpose.** The agent framework: how AI agents plan and act safely with permissioned
> tools and human oversight. **Status: FUTURE (Phase 06)** — built only after tools,
> permissions, and approval controls are proven.

## Documents

- [AgentFramework.md](./AgentFramework.md) — runtime & structure.
- [AgentLifecycle.md](./AgentLifecycle.md) — run lifecycle & state.
- [ToolCalling.md](./ToolCalling.md) — tool contracts.
- [AgentPermissions.md](./AgentPermissions.md) — permission model.
- [HumanApproval.md](./HumanApproval.md) — human-in-the-loop.

## Foundations

- Architecture: [../03-Architecture/AgentArchitecture.md](../03-Architecture/AgentArchitecture.md).
- Security: [../10-Security/AgentSecurity.md](../10-Security/AgentSecurity.md),
  [../10-Security/AIThreatModel.md](../10-Security/AIThreatModel.md).

## Non-Negotiables

1. No privilege escalation (agent ⊆ user permissions).
2. Permissioned tools only; every call authorized.
3. Human approval for consequential actions.
4. Full, replayable audit of every run.
