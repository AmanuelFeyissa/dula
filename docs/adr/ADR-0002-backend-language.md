# ADR-0002: Primary Backend Language & Framework

- Status: Accepted
- Date: 2026-08-11
- Revised: 2026-08-11 (M000 — promoted from "MVP-only Python; Go deferred" to the permanent polyglot stance below; nothing was implemented under the prior wording)
- Deciders: Architecture
- Related: [../01-Project/TechnologyStack.md](../01-Project/TechnologyStack.md)

## Context
The platform is AI/ML-heavy and must be maintainable by one team across many services,
while also ingesting security telemetry at potentially high throughput.

## Options Considered
1. **Python 3.12 + FastAPI** — native AI/ML ecosystem, async, OpenAPI, Pydantic.
2. **Go** — excellent throughput/concurrency for data-plane work; weak ML ecosystem.
3. Node/TypeScript backend — would fragment the ML story.
4. Rust — steep; reserved for rare, proven hot paths only.

## Decision (permanent)
**Python 3.12 + FastAPI is the permanent primary backend language** for services, APIs,
AI/ML, and pipelines.

**Go is an approved, permanent secondary language for high-throughput data-plane
components** (e.g. the telemetry ingestion pipeline) where measured throughput/latency
warrants it. This is a standing architectural allowance — not a deferral — used
judiciously to keep the operational surface small; the default remains Python.

## Consequences
- One primary toolchain and AI ecosystem; a sanctioned path for performance-critical
  ingestion without re-litigating language choice.
- Polyglot operational cost is accepted and bounded to data-plane services with a clear
  performance rationale.

## Compliance / Verification
- New Go services require a documented throughput/latency rationale in their design;
  everything else is Python. Any additional language requires a new ADR.
