---
title: Local Development
document_id: DEP-001
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Platform
audience: All engineers
phase: Documentation Bootstrap (M000)
related:
  - ./DockerDeployment.md
  - ../01-Project/ProjectStructure.md
---

# Local Development

> **Purpose.** Define the intended local developer experience. **Status: MVP target** —
> no code/compose files exist yet; this specifies what Phase 01 will deliver.

## 1. Goals

- One command to bring up a working local stack.
- Fast inner loop; hot reload for services/UI.
- Small local models so AI features work without a GPU.

## 2. Intended Stack (Phase 01)

- **Docker Compose** brings up: Postgres, Redis, Qdrant, OpenSearch, MinIO, Redpanda
  (Kafka API), and the app services — the same components used in production, at small scale.
- Local models via **Ollama/llama.cpp** (small, quantized) behind the LLM gateway.
- Seed data + fixtures for realistic development.

## 3. Prerequisites (planned)

- Container runtime, a task runner, and the language toolchains
  ([../01-Project/TechnologyStack.md](../01-Project/TechnologyStack.md)); exact versions
  pinned in Phase 01.

## 4. Configuration

- `.env` for local only (never for real secrets); config validated at startup.

## 5. Testing Locally

- Unit/integration tests runnable locally; see
  [../15-Testing/TestingStrategy.md](../15-Testing/TestingStrategy.md).

## 6. Parity

- Local mirrors production topology at small scale to reduce "works on my machine" drift;
  differences are documented.
