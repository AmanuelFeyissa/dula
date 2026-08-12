"""Dataset preparation (docs/08-AI/DataPipeline.md, DatasetStrategy.md).

Pulls Primus (ODC-BY/MIT) instruction/reasoning data, maps it to normalized SFT records, runs
the **safety filter → dedup → contamination check** (all from ``dula-ml``, the same code CI
runs), splits train/val, and writes conversational JSONL for the trainer. Fails hard if any
training row overlaps the held-out benchmark (contamination = 0).
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from dula_ml.contamination import assert_no_contamination, eval_hashes
from dula_ml.dedup import dedup
from dula_ml.records import SFTRecord, from_raw
from dula_ml.safety import filter_safe

SYSTEM = (
    "You are Dula, a defensive cybersecurity assistant. Answer accurately and concisely, and "
    "assist only with lawful, defensive security tasks."
)


def _load_hf(dataset_id: str, source: str, license: str) -> list[SFTRecord]:
    from datasets import load_dataset  # heavy; only needed on the runner

    records: list[SFTRecord] = []
    ds = load_dataset(dataset_id, split="train")
    for row in ds:
        rec = from_raw(dict(row), source=source, license=license)
        if rec is not None:
            records.append(rec)
    return records


def build(
    *,
    instruct_dataset: str,
    reasoning_dataset: str | None,
    license: str,
    benchmark_file: str,
    out_dir: str,
    val_fraction: float,
    seed: int,
) -> dict[str, int]:
    raw: list[SFTRecord] = _load_hf(instruct_dataset, "primus-instruct", license)
    if reasoning_dataset:
        raw += _load_hf(reasoning_dataset, "primus-reasoning", license)

    safe, dropped = filter_safe(raw)
    unique, removed = dedup(safe)

    bench = json.loads(Path(benchmark_file).read_text(encoding="utf-8"))
    assert_no_contamination(unique, eval_hashes([i["question"] for i in bench.get("mcq", [])]))

    rng = random.Random(seed)
    rng.shuffle(unique)
    n_val = max(1, int(len(unique) * val_fraction)) if unique else 0
    val, train = unique[:n_val], unique[n_val:]

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    _write_jsonl(out / "train.jsonl", train)
    _write_jsonl(out / "val.jsonl", val)

    stats = {
        "raw": len(raw),
        "dropped_unsafe": len(dropped),
        "deduped": removed,
        "train": len(train),
        "val": len(val),
    }
    print(json.dumps(stats))
    return stats


def _write_jsonl(path: Path, records: list[SFTRecord]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps({"messages": rec.to_messages(system=SYSTEM)}) + "\n")


def main() -> None:
    from dula_train.config import DatasetConfig

    parser = argparse.ArgumentParser(description="Prepare Dula AI SFT data from Primus.")
    parser.add_argument("--instruct", default=DatasetConfig().instruct_dataset)
    parser.add_argument("--reasoning", default=DatasetConfig().reasoning_dataset)
    parser.add_argument("--benchmark", default=DatasetConfig().benchmark_file)
    parser.add_argument("--out", default=DatasetConfig().out_dir)
    args = parser.parse_args()
    cfg = DatasetConfig()
    build(
        instruct_dataset=args.instruct,
        reasoning_dataset=args.reasoning,
        license=cfg.license,
        benchmark_file=args.benchmark,
        out_dir=args.out,
        val_fraction=cfg.val_fraction,
        seed=cfg.seed,
    )


if __name__ == "__main__":
    main()
