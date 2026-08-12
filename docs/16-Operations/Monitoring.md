---
title: Monitoring & Alerting
document_id: OPS-003
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Ops / Platform
audience: Ops & platform engineers
phase: Documentation Bootstrap (M000)
related:
  - ./Observability.md
  - ./IncidentManagement.md
---

# Monitoring & Alerting

> **Purpose.** Define what we watch, SLOs, and how alerts fire and route.

## 1. Golden Signals

- Latency, traffic, errors, saturation — per service; plus data-tier and inference health.

## 2. AI/Security Signals

- Model quality drift, guardrail-trigger rate, tool-call anomalies, unauthorized-action
  attempts, cross-tenant access attempts, plugin anomalies
  ([../10-Security/AIThreatModel.md](../10-Security/AIThreatModel.md)).

## 3. SLOs & Alerts

- SLOs per critical service (targets **REQUIRES DECISION**); alerts on SLO burn and on
  security-relevant events; routed to on-call via the incident process
  ([./IncidentManagement.md](./IncidentManagement.md)).

## 4. Dashboards

- Grafana dashboards per service/plane; security dashboard aggregating security-test and
  runtime security signals ([../10-Security/SecurityTesting.md](../10-Security/SecurityTesting.md)).

## 5. Model Monitoring

- Production model quality/drift/cost monitored; regression triggers rollback
  ([../09-MLOps/ModelLifecycle.md](../09-MLOps/ModelLifecycle.md)).

## 6. Alert Hygiene

- Actionable alerts only; tune to avoid fatigue; every alert links to a runbook
  ([./OperationalRunbooks.md](./OperationalRunbooks.md)).

## 7. Air-Gapped

- Alerting stays internal (e.g. internal notification channels); no external paging
  dependency required.
