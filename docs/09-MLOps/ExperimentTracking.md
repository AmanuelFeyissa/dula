---
title: Experiment Tracking
document_id: MLO-001
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: MLOps
audience: AI/ML engineers
phase: Documentation Bootstrap (M000)
related:
  - ./TrainingPipelines.md
  - ./ModelRegistry.md
---

# Experiment Tracking

> **Purpose.** Ensure every training/eval experiment is recorded and reproducible.

## 1. What Is Tracked (per run)

- Code commit + container digest
- Base model version + dataset version(s)
- Hyperparameters + config
- Hardware + seeds
- Metrics (train/val/eval) + benchmark report link
- Artifacts (adapters/weights) → registry

## 2. Tool

- **MLflow** (self-hosted) as tracking server; object storage backend (MinIO/S3) for
  artifacts; works air-gapped.

## 3. Conventions

- Experiment naming and run tags follow
  [../00-Governance/NamingConventions.md](../00-Governance/NamingConventions.md).
- Every run links to the dataset version ([./DatasetVersioning.md](./DatasetVersioning.md))
  and, if promoted, the registry entry ([./ModelRegistry.md](./ModelRegistry.md)).

## 4. Reproducibility Guarantee

- A run can be re-executed from its recorded commit, container, config, and dataset
  version to reproduce results within seed/hardware variance.

## 5. Governance

- No manual, untracked training for anything that could ship. Untracked experimentation is
  fine only in scratch, clearly non-production.
