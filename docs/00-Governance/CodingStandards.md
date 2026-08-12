---
title: Coding Standards
document_id: GOV-002
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Engineering Governance
audience: Backend, Frontend, ML, Platform engineers
phase: Documentation Bootstrap (M000)
related:
  - ../01-Project/TechnologyStack.md
  - ./NamingConventions.md
  - ./RepositoryGovernance.md
---

# Coding Standards

> **Purpose.** Define language-specific engineering standards for the technologies
> selected in [TechnologyStack.md](../01-Project/TechnologyStack.md), so code is
> consistent, reviewable, secure, and maintainable before any implementation begins.

> **Status:** These standards are **MVP** targets. No production code exists yet
> (Documentation Bootstrap phase). They become enforceable when M001 begins.

## 1. General Principles

- **Clarity over cleverness.** Optimize for the next reader.
- **Security by default.** Follow [../10-Security/SecureDevelopment.md](../10-Security/SecureDevelopment.md).
- **Fail loudly in development, degrade safely in production.**
- **No secrets in code or config committed to Git.** Use the secrets strategy in
  [../10-Security/DataSecurity.md](../10-Security/DataSecurity.md).
- **Everything typed.** Static typing is mandatory in all supported languages.
- **Small, composable units.** Prefer pure functions and dependency injection to ease
  testing (see [../15-Testing/UnitTesting.md](../15-Testing/UnitTesting.md)).

## 2. Python (Backend, AI/ML, Pipelines)

Target: **Python 3.12+**.

- **Formatting & linting:** `ruff` (lint + format) as the single source of truth.
  `black`-compatible formatting.
- **Typing:** `mypy --strict` on library code; type hints required on all public
  functions. Use `pydantic` v2 models for external data boundaries.
- **Frameworks:** `FastAPI` for services, `pydantic-settings` for config, `SQLAlchemy 2.x`
  + `Alembic` for relational persistence.
- **Async:** Prefer `async def` for I/O-bound service code; never block the event loop
  (offload CPU-bound work to a worker pool or a dedicated service).
- **Structure:** `src/` layout, package per bounded context. No business logic in route
  handlers — handlers call application services.
- **Errors:** Raise typed domain exceptions; map to HTTP at the API edge. Never leak
  stack traces or secrets in responses.
- **Logging:** Structured JSON logs via the shared logging module; never `print()`.
  See [../16-Operations/Logging.md](../16-Operations/Logging.md).
- **Dependencies:** Managed with `uv` / `pyproject.toml`; pinned lockfile committed.
- **Testing:** `pytest`, `pytest-asyncio`, coverage gate defined in
  [../15-Testing/TestingStrategy.md](../15-Testing/TestingStrategy.md).

## 3. TypeScript (Frontend)

Target: **TypeScript 5.x**, **Next.js (App Router)**, **React 18+**.

- **Formatting & linting:** `eslint` + `prettier`; `strict: true` in `tsconfig`.
- **No `any`** except at clearly-marked, justified boundaries.
- **State/data:** `TanStack Query` for server state; avoid global mutable stores unless
  justified. Server Components by default; Client Components only when needed.
- **Styling:** `Tailwind CSS` + a component library (`shadcn/ui`). See
  [../06-Frontend/UIUXGuidelines.md](../06-Frontend/UIUXGuidelines.md).
- **API access:** Generated client from the OpenAPI spec — no hand-written fetch glue
  for typed endpoints. See [../12-API/README.md](../12-API/README.md).
- **Testing:** `vitest` + `@testing-library/react`; E2E via `Playwright`.

## 4. Go (Optional High-Throughput Services)

**REQUIRES DECISION** (candidate ADR). Go is a *conditional* choice for latency- or
throughput-critical data-plane components (e.g. log ingestion) if Python proves
insufficient. If adopted:

- `gofmt`/`goimports`, `golangci-lint`, Go modules, table-driven tests.
- Standard project layout; context propagation everywhere; no naked goroutine leaks.

Until an ADR approves Go, **all services are Python** to reduce operational surface.

## 5. SQL & Migrations

- All schema changes via **Alembic** migrations — never manual DDL in production.
- Migrations are forward-only in production; reversible in development where feasible.
- See [../07-Database/MigrationStrategy.md](../07-Database/MigrationStrategy.md).

## 6. Configuration

- 12-factor style: configuration from environment / mounted secrets, not code.
- Every config key documented and validated at startup (`pydantic-settings`).
- Deployment-profile differences live in Helm values, not code branches.

## 7. Security Requirements in Code

- Validate and sanitize all external input at the boundary.
- Parameterized queries only — no string-built SQL.
- Enforce authZ at the service layer, not only the UI (see
  [../12-API/Authorization.md](../12-API/Authorization.md)).
- Treat all LLM output and all RAG-retrieved content as **untrusted** (prompt-injection
  defense — see [../10-Security/AIThreatModel.md](../10-Security/AIThreatModel.md)).
- Tool-calling code must enforce permission checks before execution (see
  [../13-Agents/AgentPermissions.md](../13-Agents/AgentPermissions.md)).

## 8. Documentation in Code

- Public modules/functions have docstrings (Python) / TSDoc (TypeScript).
- Non-obvious decisions get a comment linking the relevant ADR or doc.
- Keep comments at the density of the surrounding code — explain *why*, not *what*.

## 9. Definition of Done (Code)

A change is done only when: it compiles/type-checks, passes lint, has tests meeting the
coverage gate, passes security checks (SAST/secret scan), updates relevant docs, and is
reviewed per [RepositoryGovernance.md](./RepositoryGovernance.md).

## Related Documents

- [../01-Project/TechnologyStack.md](../01-Project/TechnologyStack.md)
- [../10-Security/SecureDevelopment.md](../10-Security/SecureDevelopment.md)
- [../15-Testing/TestingStrategy.md](../15-Testing/TestingStrategy.md)
