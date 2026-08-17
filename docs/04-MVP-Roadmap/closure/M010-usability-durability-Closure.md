---
title: Milestone Closure — M010 (Usability & Durability Hardening)
document_id: MVP-M010-CLOSURE
status: Reviewed
version: 1.0.0
last_updated: 2026-08-17
owner: Engineering
audience: Project Maintainer, Developer, Architect, Security Engineer
phase: Usability & Durability Hardening (M010)
related:
  - ../../adr/ADR-0016-agent-run-persistence.md
  - ../../13-Agents/AgentLifecycle.md
  - ../../15-Testing/IntegrationTesting.md
  - ../../PROJECT_STATE.md
  - ./README.md
---

# Milestone Closure — M010 (Usability & Durability Hardening)

> Produced per **CLAUDE.md §11.8**. M010 sits between Phase 09 (Production, M009) and the
> future Phase 10 (MLOps at scale, M011) — it is not a new "PhaseNN," so this closure has no
> paired Phase Completion Review.

- **Milestone identifier:** M010
- **Milestone name:** Usability & Durability Hardening
- **Objective:** Fix the five weaknesses a hands-on review found once Phase 09's backend was
  proven solid but the *product* was not yet usable: a read-only UI, no search/filter/pagination,
  approvers shown as opaque UUIDs, in-memory agent/playbook runs that vanish on restart, and a
  login flow that visibly bounced through Keycloak and required recreating a container to switch
  test personas.
- **Scope:** `apps/web` (UI, auth flow, Keycloak theme), `apps/platform-api` (query/write
  contract), `apps/ai-gateway` (identity attribution, durable run persistence), `packages/
  dula-agents` (async `RunStore`), `deploy/helm` (migration Job generalization), plus the E2E/
  accessibility test suite.

## Implemented functionality

Six PRs, each independently reviewed, gated, and merged (`main`, chronological):

| PR | Title | Merge |
|----|-------|-------|
| A (#17) | Dula-themed sign-in, no interstitial, real RP-initiated sign-out | `f775c85` |
| B (#18) | Approvals attributed to real usernames; stopped leaking tokens to the browser | `30c6218` |
| C (#19) | Filter, search, sort, and paginate alerts/incidents/assets | `40fe9f2` |
| D (#20) | Triage edits + create forms for alerts/incidents/assets | `f9aea21` |
| E (#21) | Durable agent/playbook run persistence (ADR-0016) | `01eb860` |
| F (#22) | Per-persona E2E suite, real accessibility fixes, next-auth bump | `4418236` |

**A — Sign-in.** A Dula-branded Keycloak login theme (`deploy/docker/keycloak/themes/dula/`)
generated from the same design tokens as the web app (`tools/sync-design-tokens.mjs`, CI-checked
for drift) replaces the default Keycloak branding. `middleware.ts` + a `/signin` route replace the
old "Continue with Keycloak" interstitial — an unauthenticated visitor now lands directly on the
themed login, no extra click. Sign-out performs real **RP-Initiated Logout** against Keycloak's
`end_session_endpoint`, so switching test personas works entirely in the browser (previously
required recreating the Keycloak container).

**B — Identity.** `ApprovalDecision` now carries both the stable OIDC `sub` (the audit anchor,
never reassignable) and a `approver_username` snapshot (display only). The UI shows "Approved by
raj," not a UUID. Also fixed a token-leak regression from an earlier session: the `/session`
route handler was returning the raw `accessToken`/`idToken` to any browser script; it now strips
them before responding.

**C — Query contract.** `TenantRepository.list()` gained `q` (substring search), `equals` (exact
filters), and `sort`, with severity/criticality ordering moved from a broken client-side sort into
a SQL `CASE` expression — correct across pages, not just within one. The frontend is entirely
URL-state-driven (`FilterBar`, `SortableHeader`, `Pagination` in `components/ui.tsx`): plain GET
forms, no client JavaScript required, native browser back/forward.

**D — Writes.** Server Actions (not client-fetch route handlers, keeping the "no JS required"
property C established) for triage edits (status/severity/assignee) and creating new
alerts/incidents/assets. Role-aware: `lib/permissions.ts` hand-mirrors the OPA `role_actions`
table so the UI hides controls a role can't use — verified as UX-only (OPA re-checks every write
server-side; the frontend map can only be *too conservative*, never too permissive).

**E — Durability (ADR-0016).** The AI Gateway gains an **optional** Postgres dependency
(`RUN_STORE=memory|postgres`, default `memory`). `RunStore` became async so `PostgresRunStore`
satisfies the same interface `InMemoryRunStore` always has; two tables (`agent_runs`,
`agent_run_steps`, own migration chain, own Alembic version table to avoid colliding with
platform-api's chain on the shared database) hold both agent and playbook runs, disambiguated by
a `kind` column. Verified with the literal acceptance test: start a run, approve it, tear the
FastAPI app down, stand up a separate instance against the same database, confirm the run and its
approval are still there over HTTP.

**F — Verification infrastructure.** The single `apps/web/e2e/smoke.spec.ts` — stale since PR A,
never caught because it isn't wired into CI — is replaced by per-persona specs (analyst triage,
responder approval, admin integrations, second-tenant isolation) plus an axe accessibility sweep.
Running the sweep for real found and fixed four live bugs: no `<main>` landmark anywhere in the
app (every page failed axe's region check), bare `<Link>`s falling back to the browser's default
hyperlink blue against the dark theme (1.93:1 contrast, real WCAG failure), and two chip color
combinations just under the 4.5:1 AA minimum (computed and corrected by hand, re-verified by
axe). Also capped Playwright's worker count (dev-server cold-compile contention was producing
false-failure timeouts) and bumped `next-auth` ten betas to clear a persistent Next.js 15
dev-mode warning, verified safe via five consecutive full E2E runs before keeping it.

## Technical changes

- `apps/web`: `middleware.ts`, `/signin`, `/auth/error` (new); `SignIn.tsx` removed; `Nav.tsx`
  sign-out; `lib/api.ts` (`getCurrentUser`, `requireAccessToken`); `lib/permissions.ts` (new);
  `lib/types.ts`; `components/ui.tsx` (`FilterBar`, `SortableHeader`, `Pagination`, `FormError`);
  per-resource `constants.ts`/`actions.ts` (new) for alerts/incidents/assets; `app/layout.tsx`
  (`<main>` landmark); `app/globals.css` + `app/design-tokens.css` (anchor baseline, contrast
  fixes); `e2e/` (5 new spec files + fixed `smoke.spec.ts`); `playwright.config.ts`.
- `apps/platform-api`: `repositories.py` (`TenantRepository.list` query contract,
  `_severity_rank`), `services.py`, `routers/{alerts,incidents,assets}.py`.
- `apps/ai-gateway`: `models.py`, `db.py`, `run_store_postgres.py` (new); `config.py`
  (`run_store`, `database_url`); `main.py` lifespan; `agents_wiring.py`/`automation_wiring.py`
  (injectable `store`); `routers/{agents,automation}.py` (async store calls); new
  `alembic/`+`alembic.ini`.
- `packages/dula-agents`: `store.py` (`RunStore` async).
- `deploy/helm/dula/templates/migration-job.yaml`: generalized from a single platform-api-only
  Job into a per-component loop over `migrations.enabled`, with a `workingDir` fix (a defect
  found while verifying it — the prior version's `alembic upgrade head` had no working directory
  set, relying on `alembic.ini`'s relative `script_location` resolving against the image's `/app`
  WORKDIR, which it never actually did).
- `deploy/docker/keycloak/themes/dula/`: new Dula login theme + token sync tooling.

## Architecture changes

- **ADR-0016** (Accepted): the AI Gateway may durably persist agent/playbook runs to Postgres,
  optional and defaulting to the prior in-memory behavior. Two services now run independent
  Alembic migration chains against one shared database — a pattern documented in the ADR
  (own version-table name per chain; no cross-service foreign keys).

## Database changes

- New tables (ai-gateway's own chain, `apps/ai-gateway/alembic/versions/0001_agent_runs.py`):
  `agent_runs`, `agent_run_steps`, RLS-scoped by `app.current_tenant` matching the domain-spine
  pattern (ADR-0006). No changes to platform-api's schema.

## API changes

- `GET /api/v1/{alerts,incidents,assets}` gained `q`, `severity`/`status`/`criticality`, `sort`
  query params (already had `limit`/`offset`).
- No AI Gateway HTTP contract changes — `RunStore` durability is an internal wiring change, not a
  new endpoint.

## Security changes

- Fixed a token-leak regression (PR B): `/api/auth/[...nextauth]`'s `/session` path no longer
  returns `accessToken`/`idToken` to browser-side scripts.
- RP-Initiated Logout properly ends the Keycloak SSO session on sign-out (previously only the
  Next.js cookie was cleared, so Keycloak silently re-authenticated).
- Role-aware UI is explicitly documented as UX-only, never authoritative (`lib/permissions.ts`);
  OPA re-evaluates every write.
- New anchor-color/contrast fixes (PR F) are accessibility, not security, but are noted here as
  they touch every page's rendering.

## Testing performed

- Backend: TDD throughout (RED-GREEN-REFACTOR per `superpowers:test-driven-development`) for the
  query contract (PR C, 26 new tests including a filter-based tenant-leak attempt) and the
  Postgres run store (PR E, 6 new tests: round-trip, tenant isolation, `kind` isolation,
  replace-not-accumulate, and the app-restart acceptance test). Full Python suite: **262 tests**
  passing (ruff, ruff format, mypy clean across `apps/platform-api`, `apps/ai-gateway`,
  `packages/dula-agents`).
- Frontend: `apps/web/e2e/` — 16 Playwright specs across 5 files, passing **5 consecutive full
  runs** locally against the real dev stack (Keycloak, Postgres, platform-api, ai-gateway) as
  6 distinct personas (maya/analyst, raj/responder, admin, tariq/second-tenant). `pnpm --filter
  web lint`/`typecheck`/`build` clean.
- Live browser verification was performed for every PR at merge time (not just asserted from test
  output), including the RP-Initiated Logout flow, the durable-run-survives-a-restart acceptance
  test (PR E, via two separate FastAPI app instances against the same database — a
  Playwright-equivalent that didn't require live OIDC), and the accessibility fixes (re-run
  through axe after each correction, not assumed fixed from the computed contrast math alone).

## Deployment validation

- `alembic upgrade head` / `downgrade base` for the AI Gateway's new chain verified against the
  dev Postgres instance already migrated by platform-api's chain — the two coexist without the
  `alembic_version` collision that was caught and fixed during this verification.
- `deploy/helm/dula/templates/migration-job.yaml`'s generalization was reasoned against the
  existing per-component `range` convention already used by `deployment.yaml`/`service.yaml` in
  the same chart (not independently `helm template`-rendered — `helm` isn't available in this
  environment; CI's `Deploy (helm + policies + air-gap)` job did render and pass it on every PR).

## Documentation completed

### Documentation Impact Assessment (CLAUDE.md §11.6)

1. **Implemented:** see "Implemented functionality" above (6 PRs, A-F).
2. **Technical docs created:** [ADR-0016](../../adr/ADR-0016-agent-run-persistence.md); this
   closure report.
3. **Technical docs updated:** [AgentLifecycle.md](../../13-Agents/AgentLifecycle.md) (run
   persistence noted, CURRENT-tagged; a retention-policy gap flagged REQUIRES DECISION),
   [IntegrationTesting.md](../../15-Testing/IntegrationTesting.md) (the new persona E2E suite,
   CURRENT-tagged), ADR index + governance ADR register, `docs/SUMMARY.md`, `CLAUDE.md` §6,
   `PROJECT_CONTEXT.md` §6, `PROJECT_STATE.md`, `RUNNING.md` (ai-gateway migration + `RUN_STORE`
   documented; an incidental `DULA_EVENTS_ENABLED` doc bug found and fixed — the real env var has
   no `DULA_` prefix for this service).
4. **User docs created:** none — no user-facing capability crossed from FUTURE to usable that
   didn't already have `docs/17-User-Documentation/` coverage from earlier milestones; the
   triage/create UI is a refinement of an already-documented capability, not a new one.
5. **User docs updated:** none required beyond what's covered by the technical updates above —
   the write UI's shape (forms, role-gating) is discoverable in-product and doesn't need a
   separate operator guide at this scale.
6. **Intentionally not created (N/A):** a stack-aware CI lane for the E2E suite (flagged as
   future work in `IntegrationTesting.md`, not silently deferred); a run-retention policy for the
   new Postgres store (flagged REQUIRES DECISION in `AgentLifecycle.md`, not silently skipped).
7. **Commands verified:** yes — every command in `RUNNING.md`'s new/changed lines was actually
   run this milestone (`alembic upgrade head` for ai-gateway, the corrected `EVENTS_ENABLED`
   var, `RUN_STORE=postgres`).
8. **Links valid:** `tools/check-doc-links.sh` passes.
9. **Diagrams:** none required new diagrams — no topology change, only an added optional data
   dependency already covered in prose by ADR-0016.
10. **Incomplete items:** none blocking.
11. **Known gaps:** `PROJECT_CONTEXT.md` §6 does not individually list ADR-0013/0014/0015 (a
    pre-existing gap from before this milestone, not introduced by it) — noted here rather than
    silently left; backfilling it is a small future cleanup, not an M010 blocker.

### Milestone Documentation Checklist (CLAUDE.md §11.7)

#### Technical Documentation
- [x] Architecture updated (ADR-0016)
- [N/A] API documentation — no formal API doc changes beyond the ADR's own description of the
  (internal, non-HTTP) `RunStore` contract; the query-param additions (PR C) are self-documenting
  via the existing router signatures and covered by the test suite, consistent with how prior
  milestones treated small param additions
- [x] Database documentation updated (ADR-0016 documents the new schema; migration file is the
  source of truth, matching the project's existing convention of not duplicating schema into prose)
- [x] Configuration documented (`RUN_STORE`, `DATABASE_URL` in RUNNING.md + ADR-0016)
- [x] Security documentation updated (token-leak fix and RP-Initiated Logout are documented in
  the PR B/A descriptions on `main`'s history; no dedicated `10-Security/` doc needed new content
  since the underlying threat model — OWASP LLM Top 10, tenant isolation — didn't change)
- [x] Deployment documentation updated (Helm migration Job generalization; RUNNING.md)
- [x] Testing documentation updated (IntegrationTesting.md)
- [N/A] Troubleshooting documentation — no new failure mode introduced that isn't already covered
  by existing 401/403/404 handling docs
- [x] Operational documentation updated (RUNNING.md)
- [x] AI/ML documentation updated where applicable (AgentLifecycle.md)
- [N/A] RAG documentation — untouched this milestone
- [x] Agent documentation updated where applicable (AgentLifecycle.md)
- [N/A] Plugin/integration documentation — untouched this milestone

#### User Documentation
- [N/A] Getting Started — unchanged
- [N/A] Installation — unchanged
- [x] Configuration guide updated (RUNNING.md)
- [~] User guide — the triage/create UI is discoverable in-product; no dedicated walkthrough
  written this milestone (partial, not blocking — matches the granularity of prior UI milestones)
- [N/A] Administrator guide — no new admin-only capability
- [N/A] Operator guide — covered by RUNNING.md's configuration updates
- [~] Feature documentation — covered by this closure report's "Implemented functionality"
  section rather than a separate feature doc, consistent with prior milestone closures' level of
  detail for UI refinements
- [N/A] Troubleshooting — no new user-facing failure mode
- [N/A] FAQ — not useful at this scale

#### Documentation Quality
- [x] Front matter follows DocumentationStandards.md
- [x] Naming follows NamingConventions.md
- [x] Relative links validated (`tools/check-doc-links.sh`)
- [N/A] Mermaid diagrams — none needed
- [x] Commands verified
- [x] Configuration examples verified
- [N/A] API examples — no new formal API doc requiring examples
- [x] No undocumented implemented functionality
- [x] No implemented functionality incorrectly marked FUTURE
- [x] No future functionality presented as CURRENT
- [x] Documentation added to `docs/SUMMARY.md`
- [N/A] Relevant glossary terms — no new domain terminology introduced this milestone
- [x] `PROJECT_CONTEXT.md` updated where necessary
- [x] `PROJECT_STATE.md` updated

## Known limitations

- The E2E persona suite (`apps/web/e2e/`) is **not wired into CI** — it requires the full Docker
  stack (Keycloak, Postgres, platform-api, ai-gateway), which the current CI workflow doesn't
  stand up. It is a manual local-verification tool today, same as `playwright.config.ts` has
  documented since before this milestone.
- The new Postgres-backed run store has **no retention/purge policy** — runs accumulate
  indefinitely (flagged REQUIRES DECISION in AgentLifecycle.md).
- `lib/permissions.ts`'s role→action map is **hand-kept in sync** with `deploy/opa/policy/
  authz.rego` — documented as a UX-only, fail-safe-conservative duplication (drift can only hide
  a control that OPA would allow, never expose one it wouldn't), but it is manual and could drift.

## Known issues

- None outstanding. All issues found during this milestone's work (token leak, stale E2E spec,
  missing `<main>` landmark, anchor color contrast, chip contrast, Alembic version-table
  collision, Helm migration Job working directory, `RUNNING.md`'s incorrect `DULA_EVENTS_ENABLED`
  var) were fixed within the same milestone, not deferred.

## Deferred work

- CI-wired E2E lane (stack-aware, future phase).
- Run-retention policy for the Postgres-backed store.
- Backfilling ADR-0013/0014/0015 into `PROJECT_CONTEXT.md` §6 (pre-existing minor gap).
- PR F's plan item to also verify durability via a literal `docker compose restart ai-gateway`
  (the AI Gateway isn't in `docker-compose.dev.yml` — it's run as a manual `uvicorn` process per
  `RUNNING.md`); the two-separate-app-instance acceptance test in PR E is the equivalent proof
  used instead and is considered sufficient.

## Lessons learned

- **Running the accessibility sweep for real, not just writing it, is what found the bugs.** All
  four PR F accessibility fixes (`<main>` landmark, anchor color, two chip contrasts) were
  invisible until axe actually executed against a live authenticated page — none would have been
  caught by code review alone.
- **Verifying a migration against the actual shared database, not just against an empty one, is
  what found the Alembic version-table collision.** The AI Gateway's migration would have looked
  correct in isolation; only running it against the same database platform-api had already
  migrated surfaced the conflict.
- **A worker-count assumption in a test config is itself something to verify, not just set.**
  The default (CPU core count) looked reasonable but reliably produced false failures against a
  dev server; only running the suite repeatedly at different settings distinguished "flaky spec"
  from "environment can't keep up."
- **A security-sensitive dependency bump is safe to make mid-milestone if the verification bar is
  raised to match the risk** — the `next-auth` bump was treated as an experiment (typecheck,
  lint, build, and the full E2E suite passing five times before keeping it), not a drive-by
  version nudge.

## Next milestone

- **Phase 10 / M011 — MLOps at scale** (Argo Workflows, MLflow, DVC, GPU serving pools) — **not
  started**; requires explicit go-ahead per `PROJECT_STATE.md`.

## Documentation gaps

- None blocking. The two intentionally-deferred items (CI E2E lane, run retention policy) are
  tracked as REQUIRES DECISION / future work in their respective docs, not silently missing.

## Final status

- **COMPLETE.** All six PRs merged to `main`, technical documentation created/updated and
  verified (link check, naming check, front matter), `PROJECT_STATE.md` and `PROJECT_CONTEXT.md`
  updated, and no known issues outstanding. The two deferred items above are explicitly scoped
  future work, not documentation gaps blocking this closure.
