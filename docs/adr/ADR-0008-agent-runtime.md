# ADR-0008: Agent Orchestration Approach

- Status: Accepted
- Date: 2026-08-11
- Deciders: AI, Security, Architecture
- Related: [../03-Architecture/AgentArchitecture.md](../03-Architecture/AgentArchitecture.md)

## Context
Agents need a graph-style plan/act loop with checkpoints, pause/resume for approval,
determinism, and full audit. The bootstrap left "custom vs LangGraph" open (review C3/O3).

## Options Considered
1. **Build on LangGraph** — graph execution, checkpoints, human-in-the-loop pause/resume
   already exist; wrap with Dula's permission/approval/audit layer.
2. Fully custom runtime — maximum control, but re-implements solved plumbing (over-engineering).
3. Higher-level frameworks (CrewAI/AutoGen) — less control over security-critical execution.

## Decision
- **Build on LangGraph** for the execution graph/checkpointing, and **own the
  security-critical layer** (tool permission checks, human-approval broker, audit,
  step/loop/time/cost limits) in Dula code — the model never self-grants tools.
- Revisit only if LangGraph cannot meet determinism/isolation/air-gapped requirements.

## Consequences
- Faster, less risky agent delivery; security controls remain first-party and testable.
- A dependency on LangGraph (permissive license — verify at adoption) is accepted; the
  agent-runtime interface abstracts it so it can be replaced.

## Compliance / Verification
- Agent-safety suite (no escalation/unauthorized actions under injection) is release-blocking
  regardless of the underlying library.
