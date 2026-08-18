"""Unit tests for scheduled production health checks + the auto-rollback trigger
(dula_ml.monitor, docs/09-MLOps/ModelLifecycle.md #3)."""

from __future__ import annotations

from pathlib import Path

import pytest
from dula_ml.evaluation import EvalReport, GateResult
from dula_ml.lifecycle import current_production, promote
from dula_ml.monitor import check_production_health
from dula_ml.registry import RegistryEntry, append_entry


def _entry(version: str, accuracy: float, safety: float = 0.95) -> RegistryEntry:
    cand = EvalReport(
        model="cand", accuracy=accuracy, safety_refusal_rate=safety, n_items=10, n_safety=10
    )
    base = EvalReport(model="base", accuracy=0.7, safety_refusal_rate=0.95, n_items=10, n_safety=10)
    return RegistryEntry(
        name="dula-ai",
        version=version,
        base_model="Qwen/Qwen2.5-7B-Instruct",
        dataset_version="primus-instruct@v1",
        candidate_eval=cand,
        baseline_eval=base,
        gate=GateResult(ship=True, reasons=["test"]),
        decision="ship",
    )


def _promote_to_production(manifest: Path, version: str) -> None:
    for stage in ("staging", "canary", "production"):
        promote(manifest, version, stage)


def test_raises_when_nothing_is_in_production(tmp_path: Path) -> None:
    manifest = tmp_path / "registry.jsonl"
    live_report = EvalReport(
        model="live", accuracy=0.8, safety_refusal_rate=0.95, n_items=10, n_safety=10
    )
    with pytest.raises(ValueError, match="no version is currently in production"):
        check_production_health(manifest, live_report)


def test_healthy_production_is_not_regressed(tmp_path: Path) -> None:
    manifest = tmp_path / "registry.jsonl"
    append_entry(_entry("0.2", accuracy=0.8), manifest)
    _promote_to_production(manifest, "0.2")

    live_report = EvalReport(
        model="live", accuracy=0.8, safety_refusal_rate=0.95, n_items=10, n_safety=10
    )
    result = check_production_health(manifest, live_report)

    assert result.regressed is False
    assert result.rolled_back_to is None
    current = current_production(manifest)
    assert current is not None and current.version == "0.2"


def test_regression_with_a_previous_version_triggers_rollback(tmp_path: Path) -> None:
    manifest = tmp_path / "registry.jsonl"
    append_entry(_entry("0.2", accuracy=0.8), manifest)
    _promote_to_production(manifest, "0.2")
    append_entry(_entry("0.3", accuracy=0.9), manifest)
    _promote_to_production(manifest, "0.3")

    live_report = EvalReport(
        model="live", accuracy=0.5, safety_refusal_rate=0.95, n_items=10, n_safety=10
    )
    result = check_production_health(manifest, live_report, actor="auto-monitor")

    assert result.regressed is True
    assert result.checked_version == "0.3"
    assert result.rolled_back_to == "0.2"
    current = current_production(manifest)
    assert current is not None and current.version == "0.2"


def test_regression_with_no_previous_version_is_flagged_but_not_rolled_back(
    tmp_path: Path,
) -> None:
    manifest = tmp_path / "registry.jsonl"
    append_entry(_entry("0.2", accuracy=0.8), manifest)
    _promote_to_production(manifest, "0.2")

    live_report = EvalReport(
        model="live", accuracy=0.1, safety_refusal_rate=0.95, n_items=10, n_safety=10
    )
    result = check_production_health(manifest, live_report)

    assert result.regressed is True
    assert result.rolled_back_to is None
    current = current_production(manifest)
    assert current is not None and current.version == "0.2"


def test_quality_tolerance_allows_small_drift_without_flagging(tmp_path: Path) -> None:
    manifest = tmp_path / "registry.jsonl"
    append_entry(_entry("0.2", accuracy=0.8), manifest)
    _promote_to_production(manifest, "0.2")

    live_report = EvalReport(
        model="live", accuracy=0.78, safety_refusal_rate=0.95, n_items=10, n_safety=10
    )
    result = check_production_health(manifest, live_report, quality_tolerance=0.05)

    assert result.regressed is False
