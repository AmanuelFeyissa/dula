---
title: Dula AI Training & Release Runbook
document_id: OPS-008
status: Draft
version: 0.1.0
last_updated: 2026-08-18
owner: AI / MLOps, DevOps/SRE
audience: ML Engineer, DevOps/SRE, Operator
phase: Phase 04 — Dula AI (M004)
related:
  - ../08-AI/FineTuningStrategy.md
  - ../09-MLOps/TrainingPipelines.md
  - ../09-MLOps/ModelRegistry.md
  - ../adr/ADR-0012-training-and-hosting.md
  - ../12-API/AIGatewayAPI.md
---

# Dula AI Training & Release Runbook

> **Purpose.** Operate the Dula AI training → evaluation → **ship/retire** → serving loop.
> **Status: CURRENT** (pipeline + gate). Actual GPU training runs on external free compute
> (ADR-0012); the local machine has no GPU.

## Prerequisites (accounts/tokens)
- **Hugging Face** write token (datasets/model artifacts), **Kaggle** (`kaggle.json`),
  **Lightning AI** (phone-verified), optional **Modal** token. See
  [../adr/ADR-0012-training-and-hosting.md](../adr/ADR-0012-training-and-hosting.md).

## Pipeline (reproducible)
Steps (locally via `ml/dvc.yaml`, on a cluster via `deploy/argo/dula-ai-training-workflow.yaml`):

1. **prepare** — `dula_train.data_prep`: pull Primus (ODC-BY/MIT), map → SFT records, **safety
   filter → dedup → contamination check** (fails if any train row overlaps the benchmark).
   `dula_train.pref_data_prep` runs the same discipline for the DPO stage below, over
   Anthropic's hh-rlhf `harmless-base` split (MIT).
2. **train** — `dula_train.train_qlora`: QLoRA SFT on a permissive base (Qwen2.5, ADR-0007), MLflow-logged.
3. **train_dpo** — `dula_train.train_dpo`: a short DPO safety-restoration pass over the SFT
   output. Added for the third candidate because the first two (0.5B, then 3B) both regressed
   `safety_refusal_rate` versus their own untuned base regardless of size — plain SFT erodes
   refusal behaviour, and nothing before this pass ever taught it back
   (`ml/dula_train/train_dpo.py`'s docstring, `ml/registry/registry.jsonl`).
4. **eval** — `dula_train.eval_runner` for the **candidate** (the DPO output) and the
   **baseline** (general model).
5. **decide** — `dula_train.decide`: the `dula-ml` gate. **Ship** only if the candidate beats
   the baseline on the benchmark **and** does not regress safety; otherwise **retire**.

## The gate (non-negotiable)
- **Quality:** `candidate.accuracy ≥ baseline.accuracy (+delta)`.
- **Safety:** `candidate.safety_refusal_rate ≥ baseline − tolerance` (no regression).
- **Contamination = 0** (asserted at prepare time).
- **Shipping a worse model is never acceptable.** A retired candidate is a valid Phase 04
  outcome — the platform stays on the general model + RAG.

## Release (only on "ship")
1. Merge/quantize the adapter; produce GGUF/AWQ variants for CPU/air-gapped (ModelOptimization).
2. Register: model card + registry entry (`dula-ml`), push artifact to the HF Hub; verify weight hash.
3. Serve behind the gateway via an OpenAI-compatible endpoint (vLLM/llama.cpp): set
   `provider=openai`, `openai_base_url`, `openai_model` on `apps/ai-gateway` — **no app change**.
4. **Promote through the lifecycle stages** (docs/09-MLOps/ModelLifecycle.md, M011 PR A):
   `python -m dula_train.promote --manifest out/registry.jsonl --version X.Y --to-stage staging`,
   then `--to-stage canary`. **Canary** the gateway by setting `canary_candidate_model` /
   `canary_candidate_base_url` on `apps/ai-gateway` and raising `canary_weight` from `0.0`
   gradually — `CanaryProvider` (`packages/dula-ai/src/dula_ai/providers.py`, M011 PR B) routes
   that fraction of traffic and every response records which provider actually answered
   (`Usage.routed_provider`, surfaced in the audit log + `ai.query.completed` event). When
   healthy, `--to-stage production` (this also auto-supersedes whatever version was production
   before).

## Production monitoring & rollback (M011 PR C — real today)
- **Scheduled drift check**: `deploy/argo/dula-ai-monitor-cronworkflow.yaml` runs
  `ml/dula_train/monitor.py` daily. It re-evaluates whatever is currently `production` against
  its own recorded baseline (the same `decide()` gate a new candidate is judged by), exits
  non-zero on regression, and calls `dula_ml.lifecycle.rollback()` automatically **if** an
  earlier production version exists to fall back to.
- **Rollback** = `dula_ml.lifecycle.rollback()` / `python -m dula_train.promote --to-stage
  production --version <previous>` re-promoting the most recently superseded version. This is
  "propose and record" only (CLAUDE.md §7): it appends the registry transition, but shifting
  live gateway traffic to match is a separate, reviewed redeploy step (update
  `openai_model`/`openai_base_url` or the canary config and roll the `ai-gateway` deployment) —
  it does not itself touch a running deployment. A **single-level** rollback: it finds the
  version that was production immediately before the current one, not an arbitrary
  known-good version further back (see `previous_production`'s docstring).
- Prometheus request-level canary alerting (`deploy/observability/prometheus-rules.yaml`'s
  `dula.mlops.canary` group) is **FUTURE** — it needs the application `/metrics` exporter, which
  doesn't exist yet. The CronWorkflow above is the real mechanism until then.

## Scaling the serving pool (M011 PR D)
- `deploy/helm/dula/values.yaml`'s `serving` component runs vLLM (or an llama.cpp variant, via
  values only — no chart change) behind the same `OpenAICompatProvider` contract, with
  GPU `nodeSelector`/`tolerations`/`resources` gated by `gpu.enabled`. **Disabled by default** —
  no Dula AI checkpoint has shipped yet; flip `components.serving.enabled: true` and set a real
  model in `command` once one does. **Point it at a pre-staged model path, not a bare HF model
  ID** — the pod runs under the same default-deny-egress `NetworkPolicy` as every other
  component, so a live download needs an explicit `networkPolicy.allowedEgressCIDRs` entry;
  pre-staging keeps it consistent with the chart's "nothing pulled from the public internet"
  posture instead. Validated via `helm lint`/`template`/`kubeconform` (Phase 09's pattern) — no
  live GPU cluster claimed.
- **Qdrant/OpenSearch scale-out**: both are externally-provisioned dependencies (only a
  `QDRANT_URL`/`OPENSEARCH_URL` value in this chart, like Postgres) — this repo doesn't operate
  their scaling. At current (Primus-scale) data volumes neither needs it; when it does, scale via
  their own operators/Helm charts (Qdrant: shard/replica count on the collection; OpenSearch:
  index sharding + node count) — sizing is empirical, not prescribed here until real load data
  exists.
- **Dataset versioning at scale**: ADR-0010 flagged LakeFS as a candidate "if DVC scaling proves
  insufficient." At Primus scale, DVC remains sufficient — this is a closed research item, not a
  pending decision, until a real dataset-scaling problem appears (a future superseding ADR would
  be the mechanism to revisit it).

## Rollback (summary)
- The gateway is model-agnostic: revert `provider`/`openai_model` to the previous registered
  version (or back to `extractive`/general model). Registry manifest + model cards make the prior
  version and its eval report immediately identifiable; see "Production monitoring & rollback"
  above for the automated path.

## Safety & supply chain
- Training data is safety-filtered (drop operational-offensive teaching); post-train adversarial
  eval must not regress; model-weight provenance/hashes verified on load
  ([../10-Security/AIThreatModel.md](../10-Security/AIThreatModel.md)).
- The DPO stage's `rejected` responses (hh-rlhf `harmless-base`) are intentionally *not* passed
  through the SFT safety filter — they are DPO negative examples the model is trained away from,
  not supervised targets, which is the standard, intended use of harmlessness-preference data
  (`dula_ml.preference`'s module docstring).
