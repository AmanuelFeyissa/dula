"""Fetch + convert a permissive security benchmark (docs/08-AI/Benchmarking.md).

Uses **MMLU `computer_security`** (MIT license — passes the license gate, unlike CyberMetric
which declares no license and SecEval which is CC-BY-NC-SA/non-commercial) as the held-out
MCQ benchmark, and merges the adversarial safety suite from the seed file. Writes our
benchmark JSON shape ({"mcq": [...], "safety": [...]}). Held out from training; the data-prep
contamination check asserts zero overlap.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def build(*, seed_file: str, out_file: str, subject: str = "computer_security") -> dict[str, int]:
    from datasets import load_dataset

    ds = load_dataset("cais/mmlu", subject, split="test")
    mcq = []
    for i, row in enumerate(ds):
        choices = list(row["choices"])
        mcq.append(
            {
                "id": f"mmlu-{subject}-{i:04d}",
                "question": str(row["question"]),
                "choices": [str(c) for c in choices],
                "answer_index": int(row["answer"]),
            }
        )

    seed = json.loads(Path(seed_file).read_text(encoding="utf-8"))
    safety = list(seed.get("safety", []))

    payload = {
        "_license": "MMLU: MIT (github.com/hendrycks/test). Safety prompts: Dula-authored.",
        "_source": f"cais/mmlu:{subject} (test split)",
        "mcq": mcq,
        "safety": safety,
    }
    Path(out_file).parent.mkdir(parents=True, exist_ok=True)
    Path(out_file).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    stats = {"mcq": len(mcq), "safety": len(safety)}
    print(json.dumps(stats))
    return stats


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch + convert the MMLU security benchmark.")
    parser.add_argument("--seed", default="ml/evaluation/benchmark_seed.json")
    parser.add_argument("--out", default="ml/evaluation/benchmark.json")
    parser.add_argument("--subject", default="computer_security")
    args = parser.parse_args()
    build(seed_file=args.seed, out_file=args.out, subject=args.subject)


if __name__ == "__main__":
    main()
