# ADR-0010: MLOps Tooling

- Status: Accepted
- Date: 2026-08-11
- Deciders: MLOps, AI
- Related: [../09-MLOps/README.md](../09-MLOps/README.md)

## Context
Reproducible, air-gap-capable model lifecycle: tracking, dataset/model versioning,
pipelines, eval gates.

## Options Considered
- Tracking/registry: **MLflow** vs W&B/ClearML (SaaS-leaning/heavier for air-gap).
- Data versioning: **DVC** vs LakeFS (scale) vs git-annex.
- Pipelines: **Argo Workflows** vs Kubeflow (heavy) vs Prefect.

## Decision
- **MLflow** (experiment tracking + model registry), **DVC** (dataset versioning over object
  storage), **Argo Workflows** (training/eval/deploy pipelines on K8s).
- All self-hosted and air-gap capable.
- **Revisit LakeFS** if DVC dataset-scaling proves insufficient (superseding ADR).

## Consequences
- Fully self-hostable lifecycle with lineage/reproducibility; heavier stack introduced
  progressively (Phase 04 → Phase 10).

## Compliance / Verification
- Every production model traces to dataset/experiment/eval report; contamination assertions
  enforced in pipelines.
