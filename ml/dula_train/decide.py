"""Ship/retire decision + registration (docs/08-AI/EvaluationStrategy.md, Phase04).

Compares a candidate eval report against the baseline (general model) using the torch-free
``dula-ml`` gate, then writes a registry entry + model card. This step is **torch-free** — it
can run anywhere, including CI — so the decision rule cannot drift from what CI tests.

Phase 04 completes whether the decision is **ship** (better + safe) or **retire** (documented,
stay on the general model). Shipping a worse model is never acceptable.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from dula_ml.evaluation import EvalReport, decide
from dula_ml.modelcard import render_model_card
from dula_ml.registry import RegistryEntry, append_entry


def make_entry(
    *,
    candidate_report: str,
    baseline_report: str,
    base_model: str,
    version: str,
    dataset_version: str,
    adapter_uri: str | None = None,
    weight_sha256: str | None = None,
    min_quality_delta: float = 0.0,
) -> RegistryEntry:
    candidate = EvalReport.model_validate_json(Path(candidate_report).read_text(encoding="utf-8"))
    baseline = EvalReport.model_validate_json(Path(baseline_report).read_text(encoding="utf-8"))
    gate = decide(candidate, baseline, min_quality_delta=min_quality_delta)
    return RegistryEntry(
        name="dula-ai",
        version=version,
        base_model=base_model,
        method="qlora",
        dataset_version=dataset_version,
        adapter_uri=adapter_uri,
        weight_sha256=weight_sha256,
        candidate_eval=candidate,
        baseline_eval=baseline,
        gate=gate,
        decision="ship" if gate.ship else "retire",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Decide ship/retire and register the candidate.")
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--base-model", default="Qwen/Qwen2.5-3B-Instruct")
    parser.add_argument("--version", default="0.1")
    parser.add_argument("--dataset-version", default="primus-instruct@v1")
    parser.add_argument("--adapter-uri", default=None)
    parser.add_argument("--manifest", default="out/registry.jsonl")
    parser.add_argument("--card-out", default="out/model_card.md")
    args = parser.parse_args()

    entry = make_entry(
        candidate_report=args.candidate,
        baseline_report=args.baseline,
        base_model=args.base_model,
        version=args.version,
        dataset_version=args.dataset_version,
        adapter_uri=args.adapter_uri,
    )
    append_entry(entry, args.manifest)
    Path(args.card_out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.card_out).write_text(render_model_card(entry), encoding="utf-8")
    print(json.dumps({"decision": entry.decision, "reasons": entry.gate.reasons}))


if __name__ == "__main__":
    main()
