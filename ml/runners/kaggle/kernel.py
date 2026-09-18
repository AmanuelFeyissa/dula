"""Kaggle script kernel: launch the Dula AI candidate pipeline on a free GPU (ADR-0012).

Push from the repo root with the Kaggle CLI (``kernel-metadata.json`` beside this file):

    kaggle kernels push -p ml/runners/kaggle
    kaggle kernels status amanuelfeyissa/dula-ai-train
    kaggle kernels output amanuelfeyissa/dula-ai-train -p out/kaggle

Kaggle can't pass arguments to a script kernel, so MODE below is the switch: run "smoke" once
(~10 GPU-min, Qwen2.5-0.5B, same code path) before "full" (7B QLoRA + DPO, several hours).
Needs a Kaggle user secret named HF_TOKEN (Add-ons -> Secrets): Primus is gated on HF.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

MODE = "full"
REPO = "https://github.com/AmanuelFeyissa/dula.git"
WORK = Path("/kaggle/working")
CLONE = WORK / "dula"
RESULT = WORK / "result"


def sh(*cmd: str, cwd: Path | None = None, check: bool = True) -> int:
    print("$ " + " ".join(cmd), flush=True)
    # Every argument is a constant from this file; nothing here comes from user input.
    return subprocess.run(list(cmd), check=check, cwd=cwd).returncode  # noqa: S603


TOKEN_FILE = Path("/kaggle/input/dula-hf-token/hf_token.txt")


def _hf_token() -> str | None:
    try:
        from kaggle_secrets import UserSecretsClient

        return str(UserSecretsClient().get_secret("HF_TOKEN")).strip() or None
    except Exception as exc:
        print(f"no HF_TOKEN secret ({exc}); trying the attached dataset", flush=True)
    if TOKEN_FILE.is_file():
        return TOKEN_FILE.read_text(encoding="utf-8").strip() or None
    return None


def main() -> None:
    # The HF token (gated Primus needs it in "full" mode; smoke does not): a Kaggle user secret
    # named HF_TOKEN, or a private one-file dataset attached as a data source.
    token = _hf_token()
    if token:
        os.environ["HF_TOKEN"] = token
        print("HF_TOKEN loaded", flush=True)
    else:
        print("no HF_TOKEN available; gated datasets will fail", flush=True)

    # Keep the HF cache off the 20 GB /kaggle/working quota; the 7B base alone is ~15 GB.
    os.environ.setdefault("HF_HOME", "/root/.cache/huggingface")
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    # Kaggle may hand out 2x T4. device_map="auto" would shard the model across both and the
    # Trainer would then wrap it in DataParallel and crash; a single T4 is the target anyway.
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"

    if CLONE.exists():
        shutil.rmtree(CLONE)
    sh("git", "clone", "--depth", "1", REPO, str(CLONE))
    sh(sys.executable, "-m", "pip", "install", "-q", "-r", "ml/requirements.txt", cwd=CLONE)
    sh(sys.executable, "-m", "pip", "install", "-q", "-e", "packages/dula-ml", cwd=CLONE)
    sh("nvidia-smi", check=False)

    os.environ["PYTHONPATH"] = "ml"
    rc = sh(sys.executable, "ml/runners/kaggle/pipeline.py", "--mode", MODE, cwd=CLONE, check=False)

    RESULT.mkdir(exist_ok=True)
    out = CLONE / "out"
    for name in (
        "result.json",
        "candidate.json",
        "baseline.json",
        "registry_entry.jsonl",
        "model_card.md",
    ):
        if (out / name).exists():
            shutil.copy2(out / name, RESULT / name)
    # The adapter is small (LoRA r=16); keep it as kernel output so it can be pulled without HF.
    for sub in ("dula-qlora-dpo", "smoke-dpo"):
        if (out / sub).is_dir():
            shutil.copytree(out / sub, RESULT / sub, dirs_exist_ok=True)
    # The clone (plus any merged model) would otherwise count against the output quota.
    shutil.rmtree(CLONE, ignore_errors=True)
    print(f"pipeline exit code {rc}; results in {RESULT}", flush=True)
    sys.exit(rc)


if __name__ == "__main__":
    main()
