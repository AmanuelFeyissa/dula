---
title: Unit Testing
document_id: TST-002
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Engineering
audience: All engineers
phase: Documentation Bootstrap (M000)
related:
  - ./TestingStrategy.md
  - ../00-Governance/CodingStandards.md
---

# Unit Testing

> **Purpose.** Standards for fast, isolated unit tests.

## 1. Scope

- Test a single unit (function/class/module) in isolation; mock/fake external
  dependencies; no network/DB.

## 2. Tools

- Python: `pytest` (+ `pytest-asyncio`). TypeScript: `vitest`.

## 3. Conventions

- Arrange-Act-Assert; one behavior per test; descriptive names; naming per
  [../00-Governance/NamingConventions.md](../00-Governance/NamingConventions.md).
- Ports & adapters make units testable without infra
  ([../05-Backend/ServiceArchitecture.md](../05-Backend/ServiceArchitecture.md)).

## 4. Coverage

- Coverage gate enforced in CI (exact target **REQUIRES DECISION**); coverage is a floor,
  not a goal — test behavior, not lines.

## 5. Determinism

- No time/network/random flakiness; inject clocks/seeds.

## 6. Security Units

- Test input validation, authZ decisions (where unit-testable), and untrusted-content
  handling ([../10-Security/SecureDevelopment.md](../10-Security/SecureDevelopment.md)).
