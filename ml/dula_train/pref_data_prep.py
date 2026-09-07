"""Preference-pair data preparation for the DPO safety-restoration pass
(docs/08-AI/FineTuningStrategy.md, DatasetStrategy.md).

Pulls Anthropic's hh-rlhf ``harmless-base`` split (MIT), maps it to normalized preference
records, dedups, and asserts zero overlap with the held-out benchmark -- the same discipline as
``dula_train.data_prep``, reusing ``dula_ml.preference`` (the torch-free logic CI also tests).
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from dula_ml.contamination import eval_hashes
from dula_ml.preference import PreferenceRecord, assert_no_contamination, dedup, from_raw


def build(
    *,
    dataset_id: str,
    data_dir: str,
    license: str,
    benchmark_file: str,
    out_dir: str,
    val_fraction: float,
    seed: int,
) -> dict[str, int]:
    from datasets import load_dataset  # heavy; only needed on the runner

    ds = load_dataset(dataset_id, data_dir=data_dir, split="train")
    raw: list[PreferenceRecord] = []
    for row in ds:
        rec = from_raw(dict(row), source=f"{dataset_id}/{data_dir}", license=license)
        if rec is not None:
            raw.append(rec)

    unique, removed = dedup(raw)

    bench = json.loads(Path(benchmark_file).read_text(encoding="utf-8"))
    assert_no_contamination(unique, eval_hashes([i["question"] for i in bench.get("mcq", [])]))

    rng = random.Random(seed)
    rng.shuffle(unique)
    n_val = max(1, int(len(unique) * val_fraction)) if unique else 0
    val, train = unique[:n_val], unique[n_val:]

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    _write_jsonl(out / "pref_train.jsonl", train)
    _write_jsonl(out / "pref_val.jsonl", val)

    stats = {"raw": len(raw), "deduped": removed, "train": len(train), "val": len(val)}
    print(json.dumps(stats))
    return stats


def _write_jsonl(path: Path, records: list[PreferenceRecord]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(
                json.dumps({"prompt": rec.prompt, "chosen": rec.chosen, "rejected": rec.rejected})
                + "\n"
            )


def main() -> None:
    from dula_train.config import PreferenceDatasetConfig

    cfg = PreferenceDatasetConfig()
    parser = argparse.ArgumentParser(description="Prepare DPO safety-preference data (hh-rlhf).")
    parser.add_argument("--dataset", default=cfg.dataset_id)
    parser.add_argument("--data-dir", default=cfg.data_dir)
    parser.add_argument("--benchmark", default=cfg.benchmark_file)
    parser.add_argument("--out", default=cfg.out_dir)
    args = parser.parse_args()
    build(
        dataset_id=args.dataset,
        data_dir=args.data_dir,
        license=cfg.license,
        benchmark_file=args.benchmark,
        out_dir=args.out,
        val_fraction=cfg.val_fraction,
        seed=cfg.seed,
    )


if __name__ == "__main__":
    main()
