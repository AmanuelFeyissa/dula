---
title: API Standards
document_id: API-001
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Backend / API
audience: API producers & consumers
phase: Documentation Bootstrap (M000)
related:
  - ./Versioning.md
  - ../00-Governance/NamingConventions.md
---

# API Standards

> **Purpose.** Consistent, predictable API design.

## 1. Style

- REST over HTTP/JSON for external APIs; gRPC for internal service-to-service where
  performance warrants.
- Resource-oriented, plural nouns, `kebab-case` paths; `snake_case` JSON/query fields
  ([../00-Governance/NamingConventions.md](../00-Governance/NamingConventions.md) §4).

## 2. Contract-First

- Define OpenAPI/proto first; generate stubs/clients; contract tests enforce conformance
  ([../15-Testing/IntegrationTesting.md](../15-Testing/IntegrationTesting.md)).

## 3. Requests & Responses

- Consistent envelope for errors (problem+json style): `type`, `title`, `status`, `detail`,
  `trace_id`. No stack traces/secrets.
- Pagination (cursor-based preferred), filtering, sorting conventions standardized.
- Idempotency keys for unsafe operations where retries occur.

## 4. Streaming

- SSE for AI/agent token/event streams; documented event schema
  ([../08-AI/InferenceArchitecture.md](../08-AI/InferenceArchitecture.md)).

## 5. Validation & Limits

- Strict input validation (pydantic); request size limits; rate limits/quotas at the
  gateway ([./Authorization.md](./Authorization.md)).

## 6. Observability

- Every request carries a trace/correlation id (OTel); consistent access logging
  ([../16-Operations/Observability.md](../16-Operations/Observability.md)).

## 7. Documentation

- Generated API reference published from the OpenAPI spec; kept in sync automatically.
