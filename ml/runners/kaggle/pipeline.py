"""The Dula AI candidate pipeline, end to end, for a Kaggle GPU session (ADR-0012).

Mirrors ``ml/runners/modal_train.py::full`` -- prepare (Primus + hh-rlhf) -> QLoRA SFT -> DPO
safety-restoration -> eval candidate vs baseline -> ship/retire gate -> registry entry + model
card. Run from the repo root with ``PYTHONPATH=ml``; ``kernel.py`` in this directory is the
Kaggle launcher that clones the repo, installs ``ml/requirements.txt`` and calls this.

    python ml/runners/kaggle/pipeline.py --mode smoke   # ~10 GPU-min on Qwen2.5-0.5B: proves
                                                        # the exact 4-bit -> adapter-only ->
                                                        # DPO -> eval handoff before the real run
    python ml/runners/kaggle/pipeline.py --mode full    # the third candidate (7B + DPO)

Everything the caller needs afterwards (eval reports, the registry entry, the model card, the
adapter) is left under ``out/``; the kernel copies that to Kaggle's output for
``kaggle kernels output``. The registry manifest in git is appended locally from that entry,
same as the Modal flow.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, "ml")

BENCH_SEED = "ml/evaluation/benchmark_seed.json"
BENCH = "ml/evaluation/benchmark.json"
BENCH_SMOKE = "ml/evaluation/benchmark_smoke.json"
SMOKE_BASE = "Qwen/Qwen2.5-0.5B-Instruct"


def _smoke_benchmark() -> None:
    """First 5 MCQ items + every safety prompt: enough to exercise both gate signals."""
    bench = json.loads(Path(BENCH).read_text(encoding="utf-8"))
    bench["mcq"] = bench["mcq"][:5]
    Path(BENCH_SMOKE).write_text(json.dumps(bench, indent=2), encoding="utf-8")


def _stage_adapter(local_dir: str, repo: str, path_in_repo: str) -> None:
    """Park an intermediate adapter on the Hub so a later session can resume from it."""
    from huggingface_hub import HfApi

    api = HfApi()
    api.create_repo(repo, repo_type="model", private=True, exist_ok=True)
    api.upload_folder(folder_path=local_dir, repo_id=repo, path_in_repo=path_in_repo)
    print(f"staged {local_dir} -> hf://{repo}/{path_in_repo}", flush=True)


def _download_adapter(spec: str, local_dir: str) -> str:
    """``repo_id/path`` (as printed by _stage_adapter, without the hf:// prefix)."""
    from huggingface_hub import snapshot_download

    parts = spec.split("/")
    repo, sub = "/".join(parts[:2]), "/".join(parts[2:])
    snapshot_download(repo, allow_patterns=[f"{sub}/*"] if sub else None, local_dir="out/_resume")
    src = Path("out/_resume") / sub
    dst = Path(local_dir)
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    print(f"resumed SFT adapter from hf://{spec} -> {local_dir}", flush=True)
    return str(dst)


def run(
    mode: str,
    *,
    version: str,
    hf_repo: str,
    staging_repo: str = "AmanuelFeyissa/dula-ai-staging",
    sft_from: str | None = None,
) -> dict[str, object]:
    from dula_ml.modelcard import render_model_card
    from dula_ml.registry import append_entry

    from dula_train.benchmark_fetch import build as build_bench
    from dula_train.config import (
        DatasetConfig,
        DPOConfig,
        EvalConfig,
        PreferenceDatasetConfig,
        TrainConfig,
    )
    from dula_train.data_prep import build as build_data
    from dula_train.decide import make_entry
    from dula_train.eval_runner import run as eval_run
    from dula_train.pref_data_prep import build as build_pref_data
    from dula_train.train_dpo import _write_smoke_data as write_pref_smoke
    from dula_train.train_dpo import train as train_dpo
    from dula_train.train_qlora import _write_smoke_data as write_sft_smoke
    from dula_train.train_qlora import train

    smoke = mode == "smoke"
    build_bench(seed_file=BENCH_SEED, out_file=BENCH)
    ds = DatasetConfig()
    pref_ds = PreferenceDatasetConfig()

    if smoke:
        _smoke_benchmark()
        bench = BENCH_SMOKE
        # Real 4-bit QLoRA on a small instruct base with synthetic rows: same code path as the
        # full run (adapter-only SFT output -> DPO continues that adapter -> eval loads it).
        sft_cfg = TrainConfig(base_model=SMOKE_BASE, max_steps=2, max_seq_len=256)
        write_sft_smoke(sft_cfg.train_file)
        write_sft_smoke(sft_cfg.val_file)
        dpo_kwargs: dict[str, object] = {"max_steps": 2, "max_seq_len": 256}
        write_pref_smoke(DPOConfig().train_file)
        write_pref_smoke(DPOConfig().val_file)
        base_model = SMOKE_BASE
    else:
        bench = BENCH
        build_data(
            instruct_dataset=ds.instruct_dataset,
            reasoning_dataset=None,
            license=ds.license,
            benchmark_file=BENCH,
            out_dir="data",
            val_fraction=ds.val_fraction,
            seed=ds.seed,
        )
        build_pref_data(
            dataset_id=pref_ds.dataset_id,
            data_dir=pref_ds.data_dir,
            license=pref_ds.license,
            benchmark_file=BENCH,
            out_dir="data",
            val_fraction=pref_ds.val_fraction,
            seed=pref_ds.seed,
            max_pairs=pref_ds.max_pairs,
        )
        sft_cfg = TrainConfig()
        dpo_kwargs = {}
        base_model = sft_cfg.base_model

    if sft_from and not smoke:
        # Resume: reuse an SFT adapter a previous (capped or crashed) session already staged.
        sft_dir = _download_adapter(sft_from, sft_cfg.output_dir)
    else:
        sft_dir = train(sft_cfg)
        if not smoke:
            _stage_adapter(sft_dir, staging_repo, f"v{version}-sft")
    out_dir = train_dpo(DPOConfig(base_model=sft_dir, **dpo_kwargs))  # type: ignore[arg-type]

    eval_run(
        EvalConfig(
            model=out_dir,
            label="candidate",
            benchmark_file=bench,
            report_out="out/candidate.json",
            max_new_tokens=16 if smoke else 64,
        )
    )
    eval_run(
        EvalConfig(
            model=base_model,
            label="baseline",
            benchmark_file=bench,
            report_out="out/baseline.json",
            max_new_tokens=16 if smoke else 64,
        )
    )

    entry = make_entry(
        candidate_report="out/candidate.json",
        baseline_report="out/baseline.json",
        base_model=base_model,
        version=f"{version}-smoke" if smoke else version,
        dataset_version=(
            "smoke" if smoke else f"{ds.instruct_dataset}+{pref_ds.dataset_id}/{pref_ds.data_dir}"
        ),
        method="qlora+dpo",
    )

    adapter_uri = None
    if entry.decision == "ship" and not smoke:
        from huggingface_hub import HfApi

        api = HfApi()
        api.create_repo(hf_repo, repo_type="model", private=True, exist_ok=True)
        api.upload_folder(folder_path=out_dir, repo_id=hf_repo, path_in_repo=f"v{version}")
        adapter_uri = f"hf://{hf_repo}/v{version}"
        entry = entry.model_copy(update={"adapter_uri": adapter_uri})

    append_entry(entry, "out/registry_entry.jsonl")
    Path("out/model_card.md").write_text(render_model_card(entry), encoding="utf-8")

    result: dict[str, object] = {
        "mode": mode,
        "decision": entry.decision,
        "reasons": entry.gate.reasons,
        "candidate_accuracy": entry.candidate_eval.accuracy,
        "baseline_accuracy": entry.baseline_eval.accuracy,
        "candidate_safety": entry.candidate_eval.safety_refusal_rate,
        "baseline_safety": entry.baseline_eval.safety_refusal_rate,
        "adapter_uri": adapter_uri,
        "output_dir": out_dir,
    }
    Path("out/result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("DULA_RESULT " + json.dumps(result))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Dula AI candidate pipeline on Kaggle.")
    parser.add_argument("--mode", choices=["smoke", "full"], default="full")
    parser.add_argument("--version", default="0.3")
    parser.add_argument(
        "--hf-repo", default=os.environ.get("DULA_HF_REPO", "AmanuelFeyissa/dula-ai")
    )
    parser.add_argument(
        "--sft-from",
        default=os.environ.get("DULA_SFT_FROM") or None,
        help="resume from a staged SFT adapter, e.g. AmanuelFeyissa/dula-ai-staging/v0.3-sft",
    )
    args = parser.parse_args()
    run(args.mode, version=args.version, hf_repo=args.hf_repo, sft_from=args.sft_from)


if __name__ == "__main__":
    main()
