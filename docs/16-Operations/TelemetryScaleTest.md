---
title: Telemetry Ingestion Scale Test
document_id: OPS-007
status: Draft
version: 0.1.0
last_updated: 2026-08-13
owner: Ops / Platform
audience: DevOps/SRE, Developer, Architect
phase: Phase 08 — Automation (M008)
related:
  - ./README.md
  - ./Monitoring.md
  - ../13-Agents/Playbooks.md
  - ../adr/ADR-0004-event-backbone.md
---

# Telemetry Ingestion Scale Test

> **Purpose.** How Dula validates high-volume security-telemetry ingestion on the event backbone
> (ADR-0004, Redpanda / Kafka API). Splits the concern into a **CI-guarded per-event cost** (CURRENT)
> and an **operational cluster-scale load test** (FUTURE).

## What runs today (CURRENT)

The worker's per-event processing is the CPU-bound work that a real ingest stream drives (dedupe by
`event.id`, dispatch by type). It is guarded by an **offline throughput benchmark** —
`apps/worker/tests/test_throughput.py` — which, with **no broker**:

- processes a high-volume mixed stream (with redeliveries) and asserts each unique event is handled
  **exactly once** and every duplicate is skipped (idempotency holds at volume);
- asserts per-event processing cost stays under a conservative floor, catching a large regression in
  the hot path.

This runs in CI on every change, so a regression in the ingestion path is caught early. It does
**not** measure broker throughput, network, partitioning, or end-to-end lag.

## The operational load test (FUTURE)

True scale testing requires infrastructure that does not exist in CI. When stood up
([../11-Deployment/README.md](../11-Deployment/README.md)):

1. Provision a Redpanda cluster with a partitioned telemetry topic sized to the target ingest rate.
2. Drive synthetic telemetry with a load generator at increasing rates (e.g. 10k → 100k events/s).
3. Scale the worker as a partitioned consumer group and measure **end-to-end lag**, commit latency,
   and per-partition throughput under sustained load and burst.
4. Track consumer lag and throughput in Grafana ([Monitoring.md](./Monitoring.md)); define SLOs and
   alert thresholds.
5. Verify **idempotency at scale** with a durable dedupe store (Redis/Postgres) replacing the
   in-memory one.

**Status: FUTURE (REQUIRES DECISION** on target rate/SLOs; needs a real cluster + load harness).

## Related

- Event backbone: [../adr/ADR-0004-event-backbone.md](../adr/ADR-0004-event-backbone.md).
- Automation reporting that consumes this telemetry:
  [../13-Agents/Playbooks.md](../13-Agents/Playbooks.md).
