---
title: Operations — Overview
document_id: OPS-000
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Ops / Platform
audience: Ops & platform engineers
phase: Documentation Bootstrap (M000)
---

# 16 — Operations

> **Purpose.** How Dula is observed, monitored, logged, and kept running — including
> incident handling, backup/recovery, and runbooks. **Status: MVP target.**

## Documents

- [Observability.md](./Observability.md) — the observability stack.
- [Logging.md](./Logging.md) · [Monitoring.md](./Monitoring.md)
- [IncidentManagement.md](./IncidentManagement.md)
- [BackupRecovery.md](./BackupRecovery.md)
- [OperationalRunbooks.md](./OperationalRunbooks.md)

## Foundations

- Stack: OpenTelemetry + Prometheus + Grafana + Loki + Tempo
  ([../01-Project/TechnologyStack.md](../01-Project/TechnologyStack.md)).
- Deployment: [../11-Deployment/README.md](../11-Deployment/README.md).

## Principle

Everything self-hostable and air-gap capable; observability data respects the same data
classification/sovereignty rules as customer data.
