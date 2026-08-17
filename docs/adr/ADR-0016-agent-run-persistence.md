# ADR-0016: Agent & Playbook Run Persistence

- Status: Accepted
- Date: 2026-08-17
- Deciders: Architecture, Platform, Security
- Related: [ADR-0002](./ADR-0002-backend-language.md), [ADR-0006](./ADR-0006-multi-tenancy.md), [ADR-0008](./ADR-0008-agent-runtime.md), [ADR-0009](./ADR-0009-auth-stack.md), [../13-Agents/AgentLifecycle.md](../13-Agents/AgentLifecycle.md), [../04-MVP-Roadmap/](../04-MVP-Roadmap/)

## Context

Agent runs (Phase 06) and playbook runs (Phase 08) pause for human approval and resume across
separate HTTP requests, so a run's state has always outlived a single request — that seam is
`dula_agents.store.RunStore`. Until now the only implementation was `InMemoryRunStore`: a
process-local dict. That is fine for the offline/air-gapped default and for tests, but it means
a consequential agent action's approval record — who approved a host isolation or a ticket
creation, and why — disappears the moment the AI Gateway process restarts. For a product whose
own agent framework promises a first-party permission/approval/**audit** layer (ADR-0008), an
audit trail that a routine deploy erases is a product defect, not an acceptable gap, once a
deployment profile cares about durability.

Milestone M010 (Usability & Durability Hardening) named this explicitly as weakness 4: *"Agent
and playbook runs are in-memory — the audit trail vanishes on restart."* Fixing it requires the
AI Gateway to gain a database dependency it has never had before (`apps/ai-gateway` has no `db.py`
prior to this ADR), which is exactly the kind of structural change ADR-0002/§10.2 of `CLAUDE.md`
reserves for an ADR rather than an ad-hoc code change.

Constraints that bound the choice:

- **Offline/air-gapped must not regress** (`GuidingPrinciples.md` §6) — the gateway must still run
  with zero external dependencies when no durability is configured.
- **Tenant isolation is non-negotiable** (ADR-0006) — a persisted run must be exactly as isolated
  as an in-memory one, including under RLS.
- **No new execution path** — `dula_agents` and `dula_automation` stay dependency-light (per their
  own module docstrings); persistence must not leak SQLAlchemy/asyncpg into either package.
- **Existing tests must keep passing unmodified** — the safety-critical agent test suite
  (`test_agents.py`, `test_automation.py`) asserts permission/approval/audit invariants against
  `InMemoryRunStore` today; none of that coverage should need to change to add durability.

## Options Considered

1. **Put persistence inside `dula_agents`/`dula_automation` directly.** Rejected: both packages are
   deliberately dependency-light (reusable outside the AI Gateway, e.g. in a future CLI or a
   different host service); adding SQLAlchemy/asyncpg there would force that dependency onto every
   consumer, including ones that will never need durability.
2. **Route runs through platform-api's existing database over HTTP.** platform-api already owns a
   Postgres schema and Alembic chain. Rejected: this makes every agent step synchronously depend on
   a second service being reachable, blurs the product boundary (agent/playbook runs are an AI
   Gateway concern per `CLAUDE.md` §3, not platform-api's), and turns a local persistence write into
   a cross-service network call on the agent's hot path.
3. **Give the AI Gateway its own Postgres dependency and its own migration chain, sharing the same
   database instance as platform-api but not its tables.** The AI Gateway already has an OIDC
   verifier and an OPA client of its own (`deps.py`); a database is the same kind of per-service
   infrastructure dependency, not a shared one. Two tables (`agent_runs`, `agent_run_steps`) hold
   both agent and playbook runs — a playbook run already **is** an agent run
   (`automation_wiring.py`) — disambiguated by a `kind` column so the two run pools stay as
   separate as the two existing `InMemoryRunStore` instances are today.

Option 3 was chosen.

## Decision

The AI Gateway gains an **optional** Postgres dependency, gated by a new `run_store` setting
(`"memory"` | `"postgres"`, default `"memory"`):

- **`RunStore` (in `dula_agents.store`) becomes async** — `save`/`get` are both `async def` — so a
  durable implementation can sit behind the exact interface `InMemoryRunStore` already satisfies.
  No other change to `dula_agents`/`dula_automation`: the runtime and its callers are unaware of
  which implementation is behind the interface.
- **`PostgresRunStore`** (new, `apps/ai-gateway/src/dula_ai_gateway/run_store_postgres.py`) is the
  durable implementation: two tables, `agent_runs` and `agent_run_steps`, with Row-Level Security
  scoped by `app.current_tenant` (the same GUC pattern as `dula_platform_api.db.get_tenant_session`,
  ADR-0006) plus an explicit `tenant_id` filter in every query — RLS and the repository filter are
  independent layers, so either one alone still fails closed. `tenant_id` is **not** a foreign key
  to platform-api's `tenants` table: the two services run independent migration chains against the
  same database (their own `alembic_version` tables, kept distinct — see Consequences), and a
  cross-service FK would make one service's migration depend on the other's having already run.
  Each `save()` replaces a run's steps wholesale (delete + reinsert) rather than diffing — traces
  are small, and this keeps every write trivially correct.
- **`InMemoryRunStore` stays the default** passed to both `build_agent_subsystem` and
  `build_automation_subsystem` (`store: RunStore | None = None`, defaulting when omitted) — the
  offline/air-gapped path and every existing test are unaffected. `main.py`'s lifespan constructs
  and injects a `PostgresRunStore` (one per subsystem, `kind="agent"` / `kind="automation"`) only
  when `settings.run_store == "postgres"`.
- **Behavioural contract preserved**: a run fetched by the wrong tenant, or under the wrong `kind`,
  returns 404 — never 403 — matching the existing assertion in
  `apps/ai-gateway/tests/test_automation.py`.

## Consequences

- **Positive**: an operator can make the audit trail durable by setting one env var
  (`RUN_STORE=postgres`) and running one Alembic migration — no code change, no new execution path,
  and the safety-critical test suite is untouched because it never constructs `PostgresRunStore`.
- **Positive**: the two services' migration chains are provably independent — verified by applying
  and reverting `apps/ai-gateway/alembic/versions/0001_agent_runs.py` against the same database
  platform-api's own chain has already migrated.
- **Negative / accepted risk**: two independent Alembic chains sharing one database means Alembic's
  default `alembic_version` bookkeeping table would collide (each chain would try to interpret the
  other's revision id). Mitigated by giving the AI Gateway's chain its own version table name
  (`dula_ai_gateway_alembic_version`, set in `apps/ai-gateway/alembic/env.py`) — a defect caught
  during this ADR's own verification, not discovered later in production.
- **Negative / accepted**: `tenant_id` without a foreign key means a stale/deleted tenant's runs are
  not automatically cascade-deleted the way platform-api's domain tables are. Acceptable for now —
  runs are an audit artifact, not live domain state — and can be revisited with a scheduled retention
  job if it becomes a real operational concern.
- **Neutral**: the Helm migration Job (`deploy/helm/dula/templates/migration-job.yaml`), previously
  hardcoded to platform-api, is generalized to run once per component that declares
  `migrations.enabled` — `ai-gateway` now sets that too.

## Compliance / Verification

- `apps/ai-gateway/tests/test_run_persistence.py` (skips cleanly when Postgres is unreachable, same
  pattern as `apps/platform-api/tests/test_domain_integration.py`): round-trip save/get, tenant
  isolation, `kind` isolation between agent and playbook run pools, and — the literal acceptance
  test for this ADR — starting a run, approving it, tearing the FastAPI app down, and confirming
  the run and its approval are still readable over HTTP from a fresh app instance against the same
  database.
- `uv run alembic upgrade head` / `downgrade base` verified against the dev Postgres instance
  already migrated by platform-api, confirming the two chains coexist without collision.
- The full existing agent/automation test suite (`test_agents.py`, `test_automation.py`) passes
  unmodified, confirming `InMemoryRunStore` remains the default and no safety-critical behaviour
  changed.
