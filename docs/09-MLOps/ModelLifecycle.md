---
title: Model Lifecycle
document_id: MLO-007
status: Draft
version: 0.1.0
last_updated: 2026-08-18
owner: MLOps / AI
audience: AI/ML & platform engineers
phase: Documentation Bootstrap (M000)
related:
  - ./ModelRegistry.md
  - ./DeploymentPipelines.md
  - ../08-AI/EvaluationStrategy.md
---

# Model Lifecycle

> **Purpose.** Tie the MLOps pieces into one end-to-end lifecycle from data to retirement,
> with monitoring and rollback.

> **Implementation status (Phase 10, CURRENT).** The state machine in §1 is implemented
> (`dula_ml.lifecycle`, `RegistryEntry.stage`) with one simplification: `Monitored` isn't a
> distinct stage (a `production` entry *is* monitored, via the scheduled job in §3), and
> `Rollback` isn't a separate stage either -- it's re-promoting a `Superseded` entry straight
> back to `Production` (`superseded -> production` is a legal edge). §3 (production monitoring)
> and §4 (rollback) are implemented as described; see
> `docs/16-Operations/DulaAITrainingRunbook.md` for how to run it.

## 1. End-to-End Lifecycle

```mermaid
stateDiagram-v2
    [*] --> DataPrep
    DataPrep --> Train
    Train --> Evaluate
    Evaluate --> Register: candidate
    Register --> Staging: eval gate pass
    Staging --> Canary
    Canary --> Production: healthy
    Canary --> Rejected: regression
    Production --> Monitored
    Monitored --> Superseded: better model promoted
    Monitored --> Rollback: incident
    Rollback --> Production
    Superseded --> Archived
    Archived --> [*]
```

## 2. Stage Ownership

| Stage | Owner | Reference |
|-------|-------|-----------|
| Data prep | Data/AI | [../08-AI/DataPipeline.md](../08-AI/DataPipeline.md) |
| Train | AI | [./TrainingPipelines.md](./TrainingPipelines.md) |
| Evaluate | AI/QA | [./EvaluationPipelines.md](./EvaluationPipelines.md) |
| Register/Deploy | MLOps | [./ModelRegistry.md](./ModelRegistry.md), [./DeploymentPipelines.md](./DeploymentPipelines.md) |
| Monitor | Ops/AI | [../16-Operations/Monitoring.md](../16-Operations/Monitoring.md) |

## 3. Production Monitoring

- Track quality signals, drift, latency, cost, safety incidents; alert on regression.
- Scheduled re-evaluation catches drift from changing knowledge indices.

## 4. Rollback & Incident

- Any safety/quality incident triggers rollback to the last-good production version and an
  incident process ([../16-Operations/IncidentManagement.md](../16-Operations/IncidentManagement.md)).

## 5. Retirement

- Superseded models are archived (retained for audit/rollback), then removed per retention
  policy.

## 6. Lineage & Audit

- Every production model traces to its data, code, config, and eval report — auditable end
  to end ([./DatasetVersioning.md](./DatasetVersioning.md)).
