# ADR-0004: Event & Streaming Backbone

- Status: Accepted
- Date: 2026-08-11
- Revised: 2026-08-11 (M000 — promoted from "NATS for MVP → Kafka on trigger" to the permanent choice below; nothing was implemented under the prior staged wording)
- Deciders: Architecture, Platform
- Related: [../03-Architecture/DataArchitecture.md](../03-Architecture/DataArchitecture.md)

## Context
The platform ingests security telemetry (potentially SIEM-scale) and needs durable
async events, streaming, and replay — plus air-gapped operability. The backbone is chosen
as the permanent, scale-capable target rather than a lightweight starter to be replaced.

## Options Considered
1. **Redpanda (Kafka API)** — Kafka-compatible, single-binary, no ZooKeeper/JVM, low ops,
   high throughput + durable replay; strong air-gapped footprint.
2. **Apache Kafka** — the streaming standard; heavier ops (equivalent capability).
3. **NATS JetStream** — lightweight and pleasant, but not aimed at SIEM-scale durable
   streaming/replay; would require adding Kafka later anyway.

## Decision (permanent)
- **Redpanda (Kafka API) is the permanent event & streaming backbone** for all async
  events, high-volume telemetry ingestion, and agent/domain events. Apache Kafka is an
  accepted drop-in equivalent for operators who prefer it (same Kafka API/contracts).
- A single backbone is used (no separate lightweight bus); synchronous request/reply is
  handled by REST/gRPC, not the event bus.

## Consequences
- SIEM-scale ingestion, durable replay, and consumer groups available from the start;
  no later backbone migration is planned. Event contracts are Kafka-API based.
- Somewhat heavier than a minimal bus; mitigated by Redpanda's single-binary simplicity
  and air-gap friendliness.

## Compliance / Verification
- Producers/consumers use the Kafka-API event abstraction; event naming is
  `domain.entity.action`; consumers are idempotent.
