"""Dula ML pipeline logic — the **torch-free**, CI-gated core of Phase 04 training.

This package holds the quality- and safety-critical logic that must be reproducible and
tested in CI **without a GPU or torch**: dataset formatting, deduplication, benchmark
contamination checks, training-data safety filtering, evaluation scoring, the **ship/retire
gate**, model-card generation, and a lightweight model registry manifest.

The heavy training itself (transformers/peft/trl on a GPU) lives in the standalone `ml/`
project and imports this package for the logic above, so the same rules apply on Kaggle /
Lightning / Modal as in CI. See docs/09-MLOps/ and docs/08-AI/FineTuningStrategy.md.
"""
