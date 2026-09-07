"""Lightweight model-registry manifest (docs/09-MLOps/ModelRegistry.md).

A portable JSON registry entry + append-only manifest, capturing everything needed to
reproduce and audit a Dula AI candidate (base model, adapter, dataset version, metrics, the
gate decision, and a weight hash for supply-chain verification). MLflow is the system of
record for experiments; this manifest travels with the artifact (e.g. to the HF Hub).
"""

from __future__ import annotations

import datetime as dt
import json
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from dula_ml.evaluation import EvalReport, GateResult


class Stage(StrEnum):
    """Registry lifecycle stages (docs/09-MLOps/ModelLifecycle.md).

    The single source of truth for valid stage names -- dula_ml.lifecycle derives its
    transition table and CLI choices from this enum rather than redeclaring the set.
    """

    STAGING = "staging"
    CANARY = "canary"
    PRODUCTION = "production"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


class RegistryEntry(BaseModel):
    name: str
    version: str
    base_model: str
    method: Literal["sft", "lora", "qlora", "qlora+dpo"] = "qlora"
    dataset_version: str
    adapter_uri: str | None = None
    artifact_uri: str | None = None
    weight_sha256: str | None = None
    candidate_eval: EvalReport
    baseline_eval: EvalReport
    gate: GateResult
    decision: Literal["ship", "retire"]
    # None until promoted past registration. A stage change is a *new* entry appended by
    # dula_ml.lifecycle.promote, never a mutation of a past one -- the manifest stays
    # append-only and auditable.
    stage: Stage | None = None
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
    """The most recently registered candidate that shipped.

    Only considers original registration entries (``stage is None``), not the lifecycle
    transitions ``dula_ml.lifecycle.promote`` appends afterwards -- a transition entry
    carries the original ``decision`` forward via ``model_copy`` (see lifecycle.py), so a
    version later moved to ``rejected``/``archived`` must not be mistaken for a fresh ship.
    """
    shipped = [e for e in load_manifest(manifest_path) if e.decision == "ship" and e.stage is None]
    return shipped[-1] if shipped else None


def to_dict(entry: RegistryEntry) -> dict[str, Any]:
    return entry.model_dump()
