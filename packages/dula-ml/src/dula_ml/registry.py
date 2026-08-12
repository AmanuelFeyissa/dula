"""Lightweight model-registry manifest (docs/09-MLOps/ModelRegistry.md).

A portable JSON registry entry + append-only manifest, capturing everything needed to
reproduce and audit a Dula AI candidate (base model, adapter, dataset version, metrics, the
gate decision, and a weight hash for supply-chain verification). MLflow is the system of
record for experiments; this manifest travels with the artifact (e.g. to the HF Hub).
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from dula_ml.evaluation import EvalReport, GateResult


class RegistryEntry(BaseModel):
    name: str
    version: str
    base_model: str
    method: Literal["sft", "lora", "qlora"] = "qlora"
    dataset_version: str
    adapter_uri: str | None = None
    artifact_uri: str | None = None
    weight_sha256: str | None = None
    candidate_eval: EvalReport
    baseline_eval: EvalReport
    gate: GateResult
    decision: Literal["ship", "retire"]
    created_at: str = Field(default_factory=lambda: dt.datetime.now(dt.UTC).isoformat())
    notes: str = ""

    def artifact_name(self) -> str:
        # dula-<base>-<task>-<method>-vX.Y (CLAUDE.md naming).
        base = self.base_model.split("/")[-1].lower()
        return f"dula-{base}-secqa-{self.method}-v{self.version}"


def append_entry(entry: RegistryEntry, manifest_path: str | Path) -> None:
    """Append an entry to the JSONL registry manifest (creating it if needed)."""
    path = Path(manifest_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(entry.model_dump_json() + "\n")


def load_manifest(manifest_path: str | Path) -> list[RegistryEntry]:
    path = Path(manifest_path)
    if not path.exists():
        return []
    entries: list[RegistryEntry] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entries.append(RegistryEntry.model_validate(json.loads(line)))
    return entries


def latest_shipped(manifest_path: str | Path) -> RegistryEntry | None:
    shipped = [e for e in load_manifest(manifest_path) if e.decision == "ship"]
    return shipped[-1] if shipped else None


def to_dict(entry: RegistryEntry) -> dict[str, Any]:
    return entry.model_dump()
