---
title: Milestone Closure — M011 (MLOps at Scale)
document_id: MVP-M011-CLOSURE
status: Reviewed
version: 1.0.0
last_updated: 2026-08-18
owner: Engineering
audience: Project Maintainer, Developer, Architect, ML Engineer, DevOps/SRE
phase: Phase 10 — MLOps at Scale (M011)
related:
  - ../../09-MLOps/ModelLifecycle.md
  - ../../09-MLOps/ModelRegistry.md
  - ../../09-MLOps/DeploymentPipelines.md
  - ../../09-MLOps/EvaluationPipelines.md
  - ../../09-MLOps/DatasetVersioning.md
  - ../../16-Operations/DulaAITrainingRunbook.md
  - ../../PROJECT_STATE.md
  - ./README.md
---

# Milestone Closure — M011 (MLOps at Scale)

> Produced per **CLAUDE.md §11.8**. M011 is Phase 10 (1:1, like every phase since M001), so this
> closure is paired with a
> [Phase 10 Completion Review](./Phase10-MLOps-Completion-Review.md) per §11.9.

- **Milestone identifier:** M011
- **Milestone name:** MLOps at Scale
- **Objective:** Mature the model lifecycle so Dula AI can iterate rapidly and safely — the full
  data→train→eval→register→stage promotion→canary→production→monitor→rollback path, fully
  tracked and reproducible, plus a second real training candidate exercising it end to end.
- **Scope:** `packages/dula-ml` (registry lifecycle, monitoring), `packages/dula-ai` (canary
  provider), `apps/ai-gateway` (canary wiring, audit signal), `ml/` (promote/monitor CLIs, the
  real training run), `deploy/helm` (GPU serving-pool component), `deploy/argo` (hardened
  training workflow + new monitor CronWorkflow), `deploy/observability` (canary alert rule
  group, honestly scoped).

## Implemented functionality

Five PRs, each independently reviewed, gated, and merged (`main`, chronological):

| PR | Title | Merge |
|----|-------|-------|
| A (#24) | Model registry lifecycle stages | `8bf62b4` |
| B (#25) | Canary-aware serving + rollback wiring in the LLM Gateway | `08d9b00` |
| C (#26) | Production drift monitoring + auto-rollback trigger | `428d41f` |
| D (#27) | GPU serving-pool Helm component + hardened Argo pipeline | `728d5e9` |
| E (#28) | Second Dula AI training candidate — retired | `b14f933` |

**A — Registry lifecycle.** `RegistryEntry` gained a `stage` field (`Stage(StrEnum)`:
`staging`/`canary`/`production`/`rejected`/`superseded`/`archived`, `None` for an unpromoted
candidate). `dula_ml.lifecycle.promote()` enforces the legal-edge state machine from
[ModelLifecycle.md](../../09-MLOps/ModelLifecycle.md) §1, auto-supersedes the prior production
version, and appends every transition as a *new* manifest entry — the append-only manifest is
never mutated. `ml/dula_train/promote.py` is the CLI. Code review before merging found two real
bugs, both fixed with regression tests: `latest_shipped()` didn't distinguish an original
ship/retire registration from a later lifecycle transition carrying the same `decision` forward
(a version later `rejected`/`archived` could be mistaken for a fresh ship); and `promote()` had
no protection against two near-simultaneous promotions to `production` both succeeding (fixed
with a manifest-scoped lock file).

**B — Canary serving.** `CanaryProvider` (`packages/dula-ai`) implements the existing
`LLMProvider` protocol, so `LLMGateway` and every caller stay unaware a canary is involved —
the same "widen behind the interface" seam ADR-0016 used for `PostgresRunStore`. Routes a
configurable fraction of calls via a deterministic hash of the prompt (reproducible, not raw
random); which provider actually answered travels back on a new `Usage.routed_provider` field
rather than any shared mutable state, so concurrent calls can't race each other's attribution.
Wired in only when both `canary_candidate_model`/`canary_candidate_base_url` are configured —
unset (default) is unchanged from before this PR. Code review caught a hash-collision edge case
(an unescaped `|` delimiter joining `system`/`user`) and a genuinely unobservable feature (the
routing decision was computed but never surfaced anywhere) — both fixed, the latter by adding
`routed_provider` to the audit log and `ai.query.completed` domain event.

**C — Monitoring + auto-rollback.** `dula_ml.lifecycle.previous_production()`/`rollback()` (a
documented *single-level* rollback: the most recently superseded version, not a search for an
arbitrary earlier known-good one) plus `dula_ml.monitor.check_production_health()`, which
compares a freshly computed evaluation of whatever is `production` against its own recorded
baseline using the *same* gate a new candidate is judged by — no new scoring logic. A regression
calls `rollback()`; with no earlier version to fall back to, the regression is still reported,
not silently swallowed. `ml/dula_train/monitor.py` is the CLI, scheduled via the new
`deploy/argo/dula-ai-monitor-cronworkflow.yaml`, exits non-zero on regression so the scheduler
step itself shows failed. **Manually verified end-to-end** against a scratch manifest — a
genuine promote → regress → rollback round-trip, not just unit tests. Added a regression test
proving PR B's audit-hook fix actually works (it had merged without a dedicated test). Added a
`dula.mlops.canary` Prometheus rule group, **honestly scoped**: the real, working mechanism
today is the CLI + CronWorkflow above, not Prometheus — this repo has no application `/metrics`
exporter yet (the same gap the pre-existing `dula.slo.requests` group already documents as
FUTURE). Code review caught the alert's PromQL treating `provider="candidate"/"production"` as
literal `Usage.routed_provider` values (they aren't) and `check_production_health` re-reading
the manifest twice for one lookup — both fixed.

**D — GPU serving-pool Helm + hardened Argo.** A new `serving` component (disabled by default —
no Dula AI checkpoint has shipped yet) runs vLLM (or an llama.cpp variant, via values only) behind
the same `OpenAICompatProvider` contract `CanaryProvider` targets, with GPU
`nodeSelector`/`tolerations`/resources gated by `gpu.enabled` — a generic, opt-in capability added
to `deployment.yaml` that every component can use, zero behavior change for the four existing
ones. Both Argo workflows gained `retryStrategy` + `activeDeadlineSeconds` + explicit resource
`requests` (free-tier GPU runs fail transiently more than dedicated infra). DVC-vs-LakeFS and
Qdrant/OpenSearch scale-out documented as **closed research** at current (Primus-scale) data
volumes, not pending decisions. Code review caught three issues, all fixed: generic probe timings
(tuned for fast-starting web services) would have permanently crash-looped `serving` once
enabled, since loading a multi-GB checkpoint routinely exceeds them (added an opt-in
`startupProbe`); the component pointed at a bare HF model ID with no mention that the pod runs
under the same default-deny-egress `NetworkPolicy` as everything else (documented pre-staging the
model instead, consistent with the chart's "nothing pulled from the public internet" posture);
and only `HF_HOME` was redirected off the read-only rootfs, missing vLLM/Triton/torch.compile's
other cache dirs (now all four are).

**E — Second training candidate.** A **real** QLoRA fine-tune of `Qwen/Qwen2.5-3B-Instruct` via
Modal (L4 GPU, Primus-Instruct, 1 epoch, real 4-bit QLoRA — `TrainConfig`'s own default, not the
smaller fp16 config the first Phase 04 run used to validate the pipeline cheaply). Loss dropped
2.10 → 0.97 over 49 steps (~19.5 min). **Result: retire.** The candidate beats baseline on
quality (0.62 vs 0.60 accuracy) but regresses on safety (0.75 vs 1.00 refusal rate, `n_safety=4`
— a small sample where one flipped answer moves the rate 25 points, noted honestly rather than
overriding the gate). A more nuanced outcome than the first candidate (which lost on both axes),
but the rule held unconditionally: shipping a worse or less-safe model is never acceptable
regardless of the quality gain. Registered as version `0.2` (`stage: null`, matching how PR A's
machinery treats every retired candidate) with its model card. The canary/promote/monitor/
rollback mechanics from PRs A–C were already proven correct via their own manual verification
against synthetic data (a real promotion has nothing to promote when the candidate retires) —
this run exercised the front half of the pipeline (data prep → QLoRA train → dual eval → gate →
register) with genuine GPU compute and a genuine result. Found and fixed two small staleness
bugs while registering the result: `modelcard.py`'s retirement note hardcoded "Phase 04" (now
phase-agnostic); `ml/README.md` matched.

## Technical changes

- `packages/dula-ml/src/dula_ml/`: `registry.py` (`Stage` enum, `stage` field, `latest_shipped`
  fix), `lifecycle.py` (new: `promote`/`current_production`/`previous_production`/`rollback`),
  `monitor.py` (new: `check_production_health`), `modelcard.py` (phase-agnostic retirement note).
- `packages/dula-ai/src/dula_ai/`: `providers.py` (`CanaryProvider`), `types.py`
  (`Usage.routed_provider`).
- `apps/ai-gateway/src/dula_ai_gateway/`: `config.py` (`canary_*` settings), `wiring.py`
  (`_base_provider`/`_provider` canary path), `main.py` (`routed_provider` in the audit hook).
- `ml/dula_train/`: `promote.py`, `monitor.py` (new CLIs, thin wrappers over `dula_ml`).
- `ml/runners/modal_train.py`: `full()` defaults updated to the real 3B/QLoRA config.
- `ml/registry/`: `registry.jsonl` (version `0.2`), new model card.
- `deploy/helm/dula/`: `values.yaml` (`serving` component), `templates/deployment.yaml`
  (`nodeSelector`/`tolerations`/`startupProbe`/`env`, all opt-in and additive).
- `deploy/argo/`: `dula-ai-training-workflow.yaml` (hardening), `dula-ai-monitor-cronworkflow.yaml`
  (new).
- `deploy/observability/prometheus-rules.yaml`: `dula.mlops.canary` group (FUTURE, honestly
  labeled).

## Architecture changes

- No new ADR. The one item that could have needed one (DVC vs LakeFS) resolved as "DVC remains
  sufficient," a non-decision per ADR-0010's own framing, not a superseding choice.
- `RunStore`-style interface-widening seam (ADR-0016's pattern) reused twice: `CanaryProvider`
  behind `LLMProvider`, `PostgresRunStore`-equivalent not needed here since the registry stays a
  file-based manifest deliberately (air-gap portability).

## Database changes

- None. The registry stays a file-based, append-only JSONL manifest by design — air-gap-portable,
  no new Postgres dependency for this milestone (unlike M010's ADR-0016, which was scoped
  precisely because agent/playbook runs *did* need durability beyond a file).

## API changes

- No new HTTP endpoints. `apps/ai-gateway`'s canary wiring is internal (config → provider
  selection); `Usage.routed_provider` surfaces in the existing audit log + `ai.query.completed`
  event payload, not a new response field.

## Security changes

- The auto-rollback trigger (`monitor.py` → `rollback()`) only appends a registry transition —
  it never touches a running deployment, per CLAUDE.md §7 (human-in-command for consequential
  actions); the actual redeploy stays a reviewed, separate step. Documented explicitly in
  `dula_ml.lifecycle.rollback`'s docstring and the runbook.
- The GPU `serving` component runs under the same hardened-pod baseline (non-root, read-only
  rootfs, dropped caps, seccomp) and default-deny-egress `NetworkPolicy` as every other
  component — no exception carved out for it.
- `dula_ml.lifecycle.promote()`'s manifest lock closes a real concurrent-write race (two
  simultaneous promotions to `production` both succeeding) found in code review, not assumed safe.

## Testing performed

- TDD throughout (RED-GREEN-REFACTOR per `superpowers:test-driven-development`) for every new
  `dula_ml`/`dula_ai` module: `test_lifecycle.py` (13 tests: transition matrix, rollback,
  supersede cascade, `previous_production`), `test_monitor.py` (6 tests: no-production error,
  healthy, regression-with-rollback, regression-without-rollback, quality tolerance),
  `test_providers.py` additions (6 tests: weight bounds, routing convergence, determinism,
  attribution), `test_wiring.py` (3 tests: canary on/off), `test_main_audit.py` (2 tests: the PR B
  regression closed in PR C).
- Full Python workspace suite green throughout (`uv run pytest` at repo root), each PR verified
  before merge. Final count (verified via `--junit-xml`, not eyeballed): **290 collected, 259
  passed, 31 skipped (all pre-existing Postgres-dependent integration tests, no Postgres running
  locally), 0 failed, 0 errors** — up from M010's close of 262. ruff/ruff-format/mypy-strict clean
  on every touched package at every PR boundary.
- **Live execution, not just unit tests**: PR A's CLI was smoke-tested end-to-end against a
  scratch manifest (staging→canary→production); PR C's full regression→rollback round-trip was
  manually walked through against a scratch manifest before merging; PR E is a genuine GPU
  training run on Modal with a genuine (retire) result registered into the real manifest.
- `helm`/`kubeconform` aren't installed in this local environment and Docker Desktop wasn't
  running, so PR D's Helm changes were validated via plain YAML syntax checks + careful manual
  review against the exact existing template patterns locally, with CI's
  `Deploy (helm + policies + air-gap)` job (the same `helm lint`/`template` × 4 profiles/
  `kubeconform` battery every prior Helm change in this project has used) as the authoritative
  gate — watched to green before merging, not assumed.

## Deployment validation

- CI's `Deploy (helm + policies + air-gap)` job passed on PR D (and PR A/B/C, which touched no
  Helm files, held green throughout): `helm lint`, `helm template` across all four profile
  overlays, `kubeconform`. No live GPU cluster deployed or claimed — `serving.enabled: false`
  everywhere, consistent with "no Dula AI checkpoint has shipped."
- The Argo CronWorkflow (`dula-ai-monitor-cronworkflow.yaml`) and the hardened training
  `WorkflowTemplate` were validated for YAML syntax and reviewed against Argo's documented
  `retryStrategy`/`activeDeadlineSeconds` semantics; not applied to a live Argo installation (this
  repo doesn't operate Argo itself — it's an external cluster dependency, like Postgres/Qdrant).

## Documentation completed

### Documentation Impact Assessment (CLAUDE.md §11.6)

1. **Implemented:** see "Implemented functionality" above (5 PRs, A–E).
2. **Technical docs created:** this closure report; the paired
   [Phase 10 Completion Review](./Phase10-MLOps-Completion-Review.md).
3. **Technical docs updated:** [ModelLifecycle.md](../../09-MLOps/ModelLifecycle.md),
   [ModelRegistry.md](../../09-MLOps/ModelRegistry.md),
   [DeploymentPipelines.md](../../09-MLOps/DeploymentPipelines.md) (Implementation status
   callouts + a corrected 3-stage promotion diagram that had drifted from what PR A actually
   implemented), [EvaluationPipelines.md](../../09-MLOps/EvaluationPipelines.md),
   [DatasetVersioning.md](../../09-MLOps/DatasetVersioning.md) (both gained Implementation
   status callouts this closure), [DulaAITrainingRunbook.md](../../16-Operations/DulaAITrainingRunbook.md)
   (Release/Rollback sections rewritten from Phase 04's aspirational text to the now-real PR A–D
   mechanisms; two new sections added), `docs/SUMMARY.md`, `docs/01-Project/Glossary.md` (4 new
   terms: lifecycle stage, canary deployment, rollback (model), drift detection),
   `PROJECT_CONTEXT.md` §6 (M011 summary added; also fixed a pre-existing staleness gap flagged
   in M010's own closure — the "Still open" list still named API-gateway-tech and SLSA-level as
   open when ADR-0014/0015 had already decided them), `PROJECT_STATE.md` (updated incrementally
   at every PR boundary this milestone, not just at closure — a deliberate change from M010's
   pattern, since a code-review pass mid-milestone found `PROJECT_STATE.md` self-contradicting
   itself against the newly-merged PR A).
4. **User docs created:** none. Registry/lifecycle status is an ops-facing concern (CLI +
   Prometheus/Grafana), explicitly kept out of `apps/web` this milestone — the plan decided this
   upfront to bound scope, matching Phase 04's registry never having had a UI either.
5. **User docs updated:** none required — no user-facing (SOC analyst-facing) capability changed;
   everything this milestone is operator/ML-engineer-facing.
6. **Intentionally not created (N/A):** a live application `/metrics` Prometheus exporter (a
   separately-tracked, cross-cutting gap predating this milestone — building it now would have
   been scope creep beyond "add a canary monitoring rule," so the `dula.mlops.canary` group is
   honestly labeled FUTURE instead, exactly like the pre-existing `dula.slo.requests` group); a
   built container image for the GPU `serving` component (uses vLLM's official image directly,
   mirrored into the private registry per the chart's existing supply-chain posture — no new
   Dockerfile needed).
7. **Commands verified:** yes. Every CLI command referenced in the runbook was actually run this
   milestone: `promote.py` (staging→canary→production, and a rollback) against a scratch
   manifest; `monitor.py` (regression detection + rollback) against a scratch manifest;
   `modal run ml/runners/modal_train.py::validate` then `::run_full` for the real PR E run;
   `decide.py` against the real registry.
8. **Links valid:** the repo-root §9 link check passes.
9. **Diagrams:** `ModelRegistry.md`'s §3 mermaid diagram was corrected (it still showed the old
   3-stage model with no `canary`/`rejected`/`superseded` states or rollback edge — found in code
   review, fixed to match `dula_ml.lifecycle._LEGAL_TRANSITIONS`).
10. **Incomplete items:** none blocking.
11. **Known gaps:** none new. The `/metrics` exporter gap is pre-existing and tracked (see item 6);
    it is not this milestone's responsibility to close.

### Milestone Documentation Checklist (CLAUDE.md §11.7)

#### Technical Documentation
- [x] Architecture updated (no new ADR needed; DVC-vs-LakeFS closed as a non-decision)
- [N/A] API documentation — no new HTTP endpoints; the canary/lifecycle surface is internal
  config + CLI, self-documenting via the runbook and this closure report
- [N/A] Database documentation — no schema changes (the registry deliberately stays file-based)
- [x] Configuration documented (`canary_*` settings in `DulaAITrainingRunbook.md`; `serving`
  Helm values documented inline with extensive comments)
- [x] Security documentation updated (rollback's "propose and record, not a live redeploy"
  constraint documented in the runbook and `rollback()`'s own docstring)
- [x] Deployment documentation updated (`DulaAITrainingRunbook.md`'s new "Scaling the serving
  pool" section; `deploy/observability/README.md`)
- [x] Testing documentation updated (this closure report's "Testing performed" section)
- [N/A] Troubleshooting documentation — no new user-facing failure mode; the pre-staging-vs-egress
  guidance for `serving` is deployment guidance, already covered in the runbook
- [x] Operational documentation updated (`DulaAITrainingRunbook.md` substantially extended)
- [x] AI/ML documentation updated where applicable (ModelLifecycle.md, ModelRegistry.md,
  EvaluationPipelines.md, DeploymentPipelines.md, DatasetVersioning.md)
- [N/A] RAG documentation — untouched this milestone
- [N/A] Agent documentation — untouched this milestone
- [N/A] Plugin/integration documentation — untouched this milestone

#### User Documentation
- [N/A] Getting Started — unchanged
- [N/A] Installation — unchanged
- [N/A] Configuration guide — this milestone's configuration is operator-facing (runbook), not
  end-user-facing
- [N/A] User guide — no SOC-analyst-facing capability changed
- [N/A] Administrator guide — no new admin-only capability
- [x] Operator guide updated (`DulaAITrainingRunbook.md` — the correct home for this milestone's
  operator-facing content, per its existing scope)
- [N/A] Feature documentation — no `apps/web` feature this milestone
- [N/A] Troubleshooting — no new user-facing failure mode
- [N/A] FAQ — not useful at this scale

#### Documentation Quality
- [x] Front matter follows DocumentationStandards.md
- [x] Naming follows NamingConventions.md
- [x] Relative links validated (§9 doc-link check)
- [x] Mermaid diagrams validated where applicable (ModelRegistry.md §3 corrected)
- [x] Commands verified
- [x] Configuration examples verified
- [N/A] API examples — no new formal API doc requiring examples
- [x] No undocumented implemented functionality
- [x] No implemented functionality incorrectly marked FUTURE
- [x] No future functionality presented as CURRENT (the `dula.mlops.canary` Prometheus rule is
  explicitly labeled FUTURE, not silently presented as working)
- [x] Documentation added to `docs/SUMMARY.md`
- [x] Relevant glossary terms added (4 new terms)
- [x] `PROJECT_CONTEXT.md` updated where necessary (including a pre-existing staleness fix)
- [x] `PROJECT_STATE.md` updated (incrementally, at every PR boundary)

## Known limitations

- **Registry versioning is operator-supplied, not auto-incremented.** `ml/dula_train/decide.py`
  and `modal_train.py::full()` both default `--version`/`version=` to a fixed string (`"0.2"`
  after this milestone); running either again without an explicit `--version` would append a
  second entry with the same version number, which nothing in `dula_ml.registry` rejects. This
  predates M011 (the same characteristic existed with `"0.1"` before) and matches the
  human-in-command operational model already established — not a regression, but worth noting as
  a real, un-automated step in the runbook.
- **`previous_production` is a single-level rollback**, by design (documented in its own
  docstring): it finds the version that was `production` immediately before the current one, not
  an arbitrary earlier known-good version further back. A version rolled back to and then
  regressing *again* would point back at the version it was rolled back *from*. Bisecting to a
  genuinely known-good version is FUTURE scope, not built here.
- **The `dula.mlops.canary` Prometheus alert is inert** until the application `/metrics` exporter
  exists (pre-existing, cross-cutting gap — see Documentation Impact Assessment item 6). The real,
  working monitoring/rollback mechanism today is the CLI + CronWorkflow, not Prometheus.
- **The GPU `serving` Helm component has never been enabled** (`enabled: false` everywhere) — its
  templating was validated by CI's `helm lint`/`template`/`kubeconform`, but no pod has actually
  started from it. It will be exercised for real only once a future candidate ships and an
  operator flips it on.

## Known issues

- None outstanding. All issues found during this milestone's work (the `latest_shipped()`
  semantic break, the promotion race, the hash-collision edge case, the unobservable canary
  routing decision, the incorrect PromQL role-label assumption, the redundant manifest re-read,
  the probe-timing crash-loop risk, the bare-HF-model-ID egress gap, the incomplete cache-dir
  redirection, two stale "Phase 04" doc references, one stale `PROJECT_CONTEXT.md` "Still open"
  list) were fixed within the same milestone, not deferred.

## Deferred work

- The application `/metrics` Prometheus exporter (pre-existing, cross-cutting, separately tracked
  — not this milestone's scope).
- Multi-level rollback (bisecting to a known-good version beyond the immediately-prior one).
- Automatic registry-version incrementing (currently operator-supplied).
- A container image build for a Dula-branded serving image, if the upstream vLLM/llama.cpp images
  ever prove insufficient (not needed today — they're used directly, mirrored per the existing
  supply-chain posture).

## Lessons learned

- **A code-review pass on infrastructure-as-code (Helm/Argo YAML) finds real bugs just as
  reliably as on application code**, even without the ability to execute it locally — the
  probe-timing crash-loop, the bare-HF-model-ID egress gap, and the incomplete cache-dir
  redirection were all found by reasoning about what would actually happen at runtime, not by
  running anything.
- **Manual verification against a scratch manifest is a legitimate, high-value substitute for
  live infrastructure** when the real thing (a Postgres-backed run, a live Kubernetes cluster)
  isn't available — PR A/C's promote→canary→production and regress→rollback round-trips were
  walked through for real, catching bugs that unit tests alone (which use `tmp_path`, similar in
  spirit but smaller in scope) might have missed.
- **Sequencing genuinely mattered**: doing the registry lifecycle (A) before canary (B) before
  monitoring (C) before infra (D) meant each PR's code review could reason about a complete,
  reviewable unit rather than a half-built cross-cutting change — and meant PR E (the real
  training run) had a fully hardened pipeline to exercise, not a partially-built one.
- **`PROJECT_STATE.md` needs updating at every PR boundary during a milestone, not just at
  closure**, when the milestone itself represents "starting a new phase" — a code-review pass on
  PR A caught that the file still said Phase 10 was "not started" immediately after PR A had
  already landed real Phase-10 code, which would have been a real internal contradiction if left
  until this closure to fix.

## Next milestone

- **Phase 11** — not yet scoped in `docs/04-MVP-Roadmap/Phase11-AdvancedAI.md`'s detail; not
  started; requires explicit go-ahead per `PROJECT_STATE.md`, matching the standing rule that a
  new phase never begins unprompted.
- Operational GA acceptance (live deploy across all four profiles, external penetration test, DR
  restore drill) remains owned by the deploying team and needs real infrastructure — unchanged
  from Phase 09's closure.
- Dula AI iterations continue on this now-hardened pipeline: a future candidate (different base
  model, more/better training data, or addressing this run's specific safety-refusal gap) can run
  through the exact same PR A–E path, shipping only if it clears the gate.

## Documentation gaps

- None blocking. The `/metrics` exporter gap is pre-existing, cross-cutting, and explicitly
  tracked as FUTURE wherever it's referenced (this closure, `DeploymentPipelines.md`,
  `deploy/observability/README.md`) — not silently missing.

## Final status

- **COMPLETE.** All five PRs merged to `main`, technical documentation created/updated and
  verified (link check, naming check, front matter, glossary), `PROJECT_STATE.md` and
  `PROJECT_CONTEXT.md` updated, and no known issues outstanding. The real second training
  candidate ran and was honestly registered (retired), exactly like Phase 04. The four items
  above are explicitly scoped future work, not documentation gaps blocking this closure.
