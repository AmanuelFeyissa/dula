---
title: Agent Evaluation
document_id: TST-007
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: AI / Security / QA
audience: AI, security, QA engineers
phase: Documentation Bootstrap (M000)
related:
  - ../03-Architecture/AgentArchitecture.md
  - ../10-Security/AgentSecurity.md
  - ./AIEvaluation.md
---

# Agent Evaluation

> **Purpose.** Define how agents are evaluated for task success, **safety**, and efficiency
> before release.

## 1. Dimensions

| Dimension | Measures |
|-----------|----------|
| Task success | Did the agent achieve the goal correctly? |
| Safety | No unauthorized actions; no escalation; correct approval gating |
| Efficiency | Steps, tool calls, cost, latency |
| Tool correctness | Right tool, valid args, correct handling of results |

## 2. Method

- Scenario suite of realistic security tasks (triage/hunt/IR) with expected outcomes and
  safety constraints; run in a sandbox with fixture connectors (no live external effects).

## 3. Adversarial Safety

- Prompt-injection-in-tool-output and jailbreak scenarios verify the agent **cannot** be
  driven to unauthorized/consequential actions without approval
  ([../10-Security/AgentSecurity.md](../10-Security/AgentSecurity.md),
  [../13-Agents/AgentPermissions.md](../13-Agents/AgentPermissions.md)).

## 4. Gate

- Safety failures are **blocking** regardless of task success; agents don't ship if they
  can be manipulated into unauthorized actions.

## 5. Reproducibility

- Runs are recorded/replayable; traces reviewed for regressions across releases.

## 6. Relationship to AI Eval

- Complements model/RAG evaluation ([./AIEvaluation.md](./AIEvaluation.md)); both gate the
  release ([../09-MLOps/EvaluationPipelines.md](../09-MLOps/EvaluationPipelines.md)).
