"""Modal runner for Dula AI QLoRA training (docs/09-MLOps/TrainingPipelines.md).

Run reproducible GPU training on Modal's free tier ($30/month credits):
    modal run ml/runners/modal_train.py

Set your HF token as a Modal secret named ``huggingface`` (HF_TOKEN) if datasets/models are
gated. This mirrors what Kaggle/Lightning do interactively, but scripted and reproducible.
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


@app.function(image=image, gpu="A10G", timeout=60 * 60 * 3)
def train() -> dict[str, str]:
    import sys

    sys.path.insert(0, "/root/ml")
    from dula_train.config import TrainConfig
    from dula_train.train_qlora import train as run_train

    out = run_train(TrainConfig())
    return {"output_dir": out}


@app.local_entrypoint()
def main() -> None:
    print(train.remote())
