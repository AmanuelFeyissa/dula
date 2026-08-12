"""Unit tests for the registry manifest and model-card rendering."""

from __future__ import annotations

from pathlib import Path

from dula_ml.evaluation import EvalReport, GateResult
from dula_ml.modelcard import render_model_card
from dula_ml.registry import RegistryEntry, append_entry, latest_shipped, load_manifest


def _entry(decision: str, version: str = "0.1") -> RegistryEntry:
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


def test_artifact_name_follows_convention() -> None:
    assert _entry("ship").artifact_name() == "dula-qwen2.5-7b-instruct-secqa-qlora-v0.1"


def test_manifest_roundtrip_and_latest_shipped(tmp_path: Path) -> None:
    manifest = tmp_path / "registry.jsonl"
    append_entry(_entry("retire", "0.1"), manifest)
    append_entry(_entry("ship", "0.2"), manifest)
    entries = load_manifest(manifest)
    assert len(entries) == 2
    latest = latest_shipped(manifest)
    assert latest is not None and latest.version == "0.2"


def test_model_card_states_decision(tmp_path: Path) -> None:
    ship_card = render_model_card(_entry("ship"))
    assert "SHIP" in ship_card and "Benchmark accuracy" in ship_card
    retire_card = render_model_card(_entry("retire"))
    assert "RETIRE" in retire_card and "Retirement note" in retire_card
