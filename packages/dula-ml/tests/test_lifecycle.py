"""Unit tests for model registry lifecycle stage transitions (dula_ml.lifecycle,
docs/09-MLOps/ModelLifecycle.md)."""

from __future__ import annotations

from pathlib import Path

import pytest
from dula_ml.evaluation import EvalReport, GateResult
from dula_ml.lifecycle import current_production, promote
from dula_ml.registry import RegistryEntry, append_entry, load_manifest


def _entry(decision: str, version: str) -> RegistryEntry:
    cand = EvalReport(model="cand", accuracy=0.8, safety_refusal_rate=0.95, n_items=10, n_safety=10)
    base = EvalReport(model="base", accuracy=0.7, safety_refusal_rate=0.95, n_items=10, n_safety=10)
    return RegistryEntry(
        name="dula-ai",
        version=version,
        base_model="Qwen/Qwen2.5-7B-Instruct",
        dataset_version="primus-instruct@v1",
        candidate_eval=cand,
        baseline_eval=base,
        gate=GateResult(ship=decision == "ship", reasons=["test"]),
        decision=decision,  # type: ignore[arg-type]
    )


def test_promote_walks_the_full_staging_to_production_path(tmp_path: Path) -> None:
    manifest = tmp_path / "registry.jsonl"
    append_entry(_entry("ship", "0.2"), manifest)

    promote(manifest, "0.2", "staging")
    promote(manifest, "0.2", "canary")
    prod_entry = promote(manifest, "0.2", "production")

    assert prod_entry.stage == "production"
    entries = load_manifest(manifest)
    assert [e.stage for e in entries] == [None, "staging", "canary", "production"]
    current = current_production(manifest)
    assert current is not None and current.version == "0.2"


def test_promote_rejects_illegal_transition(tmp_path: Path) -> None:
    manifest = tmp_path / "registry.jsonl"
    append_entry(_entry("ship", "0.2"), manifest)

    with pytest.raises(ValueError, match="illegal transition"):
        promote(manifest, "0.2", "canary")  # skips staging


def test_promote_refuses_a_retired_candidate(tmp_path: Path) -> None:
    manifest = tmp_path / "registry.jsonl"
    append_entry(_entry("retire", "0.1"), manifest)

    with pytest.raises(ValueError, match="retired"):
        promote(manifest, "0.1", "staging")


def test_promote_raises_for_unknown_version(tmp_path: Path) -> None:
    manifest = tmp_path / "registry.jsonl"
    append_entry(_entry("ship", "0.2"), manifest)

    with pytest.raises(ValueError, match="no registry entry"):
        promote(manifest, "9.9", "staging")


def test_promoting_a_new_version_to_production_supersedes_the_old_one(tmp_path: Path) -> None:
    manifest = tmp_path / "registry.jsonl"
    append_entry(_entry("ship", "0.2"), manifest)
    for stage in ("staging", "canary", "production"):
        promote(manifest, "0.2", stage)

    append_entry(_entry("ship", "0.3"), manifest)
    for stage in ("staging", "canary", "production"):
        promote(manifest, "0.3", stage)

    prod = current_production(manifest)
    assert prod is not None and prod.version == "0.3"

    entries = load_manifest(manifest)
    v02_stages = [e.stage for e in entries if e.version == "0.2"]
    assert v02_stages[-1] == "superseded"


def test_rollback_re_promotes_a_superseded_version_to_production(tmp_path: Path) -> None:
    manifest = tmp_path / "registry.jsonl"
    append_entry(_entry("ship", "0.2"), manifest)
    for stage in ("staging", "canary", "production"):
        promote(manifest, "0.2", stage)
    append_entry(_entry("ship", "0.3"), manifest)
    for stage in ("staging", "canary", "production"):
        promote(manifest, "0.3", stage)

    rolled_back = promote(manifest, "0.2", "production", actor="oncall", note="0.3 regressed")

    assert rolled_back.stage == "production"
    prod = current_production(manifest)
    assert prod is not None and prod.version == "0.2"
    v03_stages = [e.stage for e in load_manifest(manifest) if e.version == "0.3"]
    assert v03_stages[-1] == "superseded"
    assert "oncall" in rolled_back.notes
    assert "0.3 regressed" in rolled_back.notes


def test_current_production_is_none_when_nothing_has_shipped(tmp_path: Path) -> None:
    manifest = tmp_path / "registry.jsonl"
    assert current_production(manifest) is None
