---
title: Backend Development
document_id: BE-003
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Backend
audience: Backend engineers
phase: Documentation Bootstrap (M000)
related:
  - ../00-Governance/CodingStandards.md
  - ../15-Testing/TestingStrategy.md
---

# Backend Development

> **Purpose.** Practical backend development practices for contributors. **Status: MVP** —
> scaffolding delivered in Phase 01.

## 1. Toolchain

- Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 + Alembic, `uv`, `ruff`, `mypy --strict`,
  `pytest` ([../00-Governance/CodingStandards.md](../00-Governance/CodingStandards.md)).

## 2. Project Conventions

- `src/` layout; package per bounded context; ports & adapters
  ([./ServiceArchitecture.md](./ServiceArchitecture.md)).
- Naming per [../00-Governance/NamingConventions.md](../00-Governance/NamingConventions.md).

## 3. Local Dev

- Compose-based stack ([../11-Deployment/LocalDevelopment.md](../11-Deployment/LocalDevelopment.md));
  seed data; hot reload.

## 4. Testing

- Unit + integration; coverage gate; contract tests against OpenAPI
  ([../15-Testing/TestingStrategy.md](../15-Testing/TestingStrategy.md)).

## 5. Security in Code

- Input validation, parameterized queries, authZ at service layer, untrusted AI/plugin
  content ([../10-Security/SecureDevelopment.md](../10-Security/SecureDevelopment.md)).

## 6. Definition of Done

- Compiles/type-checks, lint clean, tests pass coverage gate, security scans pass, docs
  updated, reviewed ([../00-Governance/RepositoryGovernance.md](../00-Governance/RepositoryGovernance.md)).
