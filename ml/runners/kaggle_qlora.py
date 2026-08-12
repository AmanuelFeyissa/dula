"""Kaggle / Colab / Lightning cell script for Dula AI QLoRA training.

Paste into a Kaggle notebook (GPU T4×2) or run in a Lightning Studio / Colab cell. Kaggle gives
~30 GPU hrs/week; QLoRA on a 3B–7B base fits a single T4. Steps:

    !git clone https://github.com/AmanuelFeyissa/dula.git && cd dula
    !pip install -r ml/requirements.txt && pip install -e packages/dula-ml
    # (optional) huggingface-cli login   # if datasets/models are gated
    !cd dula && python -m dula_train.data_prep --out ml/data
    !cd dula && PYTHONPATH=ml python -m dula_train.train_qlora
    !cd dula && PYTHONPATH=ml python -m dula_train.eval_runner --model out/dula-qlora --label candidate --out out/candidate.json
    !cd dula && PYTHONPATH=ml python -m dula_train.eval_runner --model Qwen/Qwen2.5-3B-Instruct --label baseline --out out/baseline.json
    !cd dula && PYTHONPATH=ml python -m dula_train.decide --candidate out/candidate.json --baseline out/baseline.json

The final step prints the ship/retire decision and writes a model card + registry entry.
"""

from __future__ import annotations


def main() -> None:
    import sys

    sys.path.insert(0, "ml")
    from dula_train.config import TrainConfig
    from dula_train.train_qlora import train

    train(TrainConfig())


if __name__ == "__main__":
    main()
