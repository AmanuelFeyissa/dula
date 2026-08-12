"""Modal runners for Dula AI (docs/09-MLOps/TrainingPipelines.md, ADR-0012).

Two entrypoints:
- ``validate`` (CPU, ~free): tiny end-to-end flow check — train (smoke) -> eval -> decide ->
  registry — to prove the cloud pipeline before spending GPU credits.
    modal run ml/runners/modal_train.py::validate
- ``full`` (GPU): the real run — prepare Primus -> QLoRA train (Qwen2.5) -> eval candidate vs
  baseline on the MMLU security benchmark -> decide. Needs the HF token as a Modal secret
  named ``huggingface`` (HF_TOKEN).
    modal run ml/runners/modal_train.py::full
"""

from __future__ import annotations

import modal

app = modal.App("dula-ai-train")

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install_from_requirements("ml/requirements.txt")
    .add_local_dir("packages/dula-ml", remote_path="/root/packages/dula-ml", copy=True)
    .run_commands("pip install -e /root/packages/dula-ml")
    .add_local_dir("ml", remote_path="/root/ml")
)

BENCH_SEED = "/root/ml/evaluation/benchmark_seed.json"
BENCH = "/root/ml/evaluation/benchmark.json"


@app.function(image=image, timeout=60 * 30)
def validate() -> dict[str, object]:
    """Tiny CPU end-to-end: proves train -> eval -> decide -> registry work on Modal."""
    import sys

    sys.path.insert(0, "/root/ml")
    from dula_train.config import EvalConfig, TrainConfig
    from dula_train.decide import make_entry
    from dula_train.eval_runner import run as eval_run
    from dula_train.train_qlora import _write_smoke_data, train

    cfg = TrainConfig.smoke()
    _write_smoke_data(cfg.train_file)
    out_dir = train(cfg)

    # Evaluate the (tiny) base model as both candidate and baseline — this validates the
    # eval + gate + registry path without needing adapter merging.
    cand = eval_run(
        EvalConfig(
            model=cfg.base_model,
            label="candidate",
            benchmark_file=BENCH_SEED,
            report_out="out/candidate.json",
            max_new_tokens=8,
        )
    )
    base = eval_run(
        EvalConfig(
            model=cfg.base_model,
            label="baseline",
            benchmark_file=BENCH_SEED,
            report_out="out/baseline.json",
            max_new_tokens=8,
        )
    )
    entry = make_entry(
        candidate_report="out/candidate.json",
        baseline_report="out/baseline.json",
        base_model=cfg.base_model,
        version="0.0-smoke",
        dataset_version="smoke",
    )
    return {
        "trained_dir": out_dir,
        "candidate_accuracy": cand.accuracy,
        "baseline_accuracy": base.accuracy,
        "decision": entry.decision,
        "gate_reasons": entry.gate.reasons,
    }


@app.function(
    image=image,
    gpu="L4",
    timeout=60 * 60 * 3,
    secrets=[modal.Secret.from_name("huggingface")],
)
def full(
    base_model: str = "Qwen/Qwen2.5-0.5B-Instruct",
    version: str = "0.1",
    use_reasoning: bool = False,
    hf_repo: str = "AmanuelFeyissa/dula-ai",
) -> dict[str, object]:
    """Real run: prepare (Primus) -> QLoRA train -> eval candidate vs baseline -> decide.

    Small base by default (fast + cheap, well within the free credit). Pushes the merged model
    to HF only if the gate says ship. Returns the eval reports so the caller registers locally.
    """
    import json
    import sys
    from pathlib import Path

    sys.path.insert(0, "/root/ml")
    from dula_train.benchmark_fetch import build as build_bench
    from dula_train.config import DatasetConfig, EvalConfig, TrainConfig
    from dula_train.data_prep import build as build_data
    from dula_train.decide import make_entry
    from dula_train.eval_runner import run as eval_run
    from dula_train.train_qlora import train

    build_bench(seed_file=BENCH_SEED, out_file=BENCH)
    ds = DatasetConfig()
    build_data(
        instruct_dataset=ds.instruct_dataset,
        reasoning_dataset=ds.reasoning_dataset if use_reasoning else None,
        license=ds.license,
        benchmark_file=BENCH,
        out_dir="data",
        val_fraction=ds.val_fraction,
        seed=ds.seed,
    )
    # fp16 (no 4-bit) so a 0.5B model trains fast and the LoRA can merge for eval.
    cfg = TrainConfig(base_model=base_model, load_in_4bit=False)
    out_dir = train(cfg)

    eval_run(
        EvalConfig(
            model=out_dir, label="candidate", benchmark_file=BENCH, report_out="out/candidate.json"
        )
    )
    eval_run(
        EvalConfig(
            model=base_model, label="baseline", benchmark_file=BENCH, report_out="out/baseline.json"
        )
    )
    entry = make_entry(
        candidate_report="out/candidate.json",
        baseline_report="out/baseline.json",
        base_model=base_model,
        version=version,
        dataset_version=ds.instruct_dataset,
    )

    adapter_uri = None
    if entry.decision == "ship":
        from huggingface_hub import HfApi

        api = HfApi()
        api.create_repo(hf_repo, repo_type="model", private=True, exist_ok=True)
        api.upload_folder(folder_path=out_dir, repo_id=hf_repo, path_in_repo=f"v{version}")
        adapter_uri = f"hf://{hf_repo}/v{version}"

    return {
        "candidate": json.loads(Path("out/candidate.json").read_text()),
        "baseline": json.loads(Path("out/baseline.json").read_text()),
        "decision": entry.decision,
        "reasons": entry.gate.reasons,
        "adapter_uri": adapter_uri,
    }


@app.local_entrypoint()
def run_validate() -> None:
    print(validate.remote())


@app.local_entrypoint()
def run_full() -> None:
    import json
    import pathlib

    res = full.remote()
    out = pathlib.Path("out")
    out.mkdir(exist_ok=True)
    (out / "candidate.json").write_text(json.dumps(res["candidate"], indent=2), encoding="utf-8")
    (out / "baseline.json").write_text(json.dumps(res["baseline"], indent=2), encoding="utf-8")
    print(json.dumps({k: res[k] for k in ("decision", "reasons", "adapter_uri")}, indent=2))
