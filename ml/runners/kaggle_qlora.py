"""Kaggle / Colab / Lightning cell script for Dula AI QLoRA + DPO training.

Paste into a Kaggle notebook (GPU T4×2) or run in a Lightning Studio / Colab cell. Kaggle gives
~30 GPU hrs/week; QLoRA on a 7B base fits a single T4. This is the third Dula AI candidate:
7B (up from 3B) plus a DPO safety-restoration pass, because the first two candidates (0.5B,
3B) both regressed safety_refusal_rate vs their own untuned base regardless of size -- see
ml/dula_train/train_dpo.py's docstring and ml/registry/registry.jsonl. Steps:

    !git clone https://github.com/AmanuelFeyissa/dula.git && cd dula
    !pip install -r ml/requirements.txt && pip install -e packages/dula-ml
    !huggingface-cli login   # needed: Qwen2.5-7B-Instruct + hh-rlhf are both ungated but a
                             # token raises HF's anonymous rate limit; Primus needs one regardless
    !cd dula && python -m dula_train.data_prep --out ml/data
    !cd dula && python -m dula_train.pref_data_prep --out ml/data
    !cd dula && PYTHONPATH=ml python -m dula_train.train_qlora
    !cd dula && PYTHONPATH=ml python -m dula_train.train_dpo --base-model out/dula-qlora
    !cd dula && PYTHONPATH=ml python -m dula_train.eval_runner --model out/dula-qlora-dpo --label candidate --out out/candidate.json
    !cd dula && PYTHONPATH=ml python -m dula_train.eval_runner --model Qwen/Qwen2.5-7B-Instruct --label baseline --out out/baseline.json
    !cd dula && PYTHONPATH=ml python -m dula_train.decide --candidate out/candidate.json --baseline out/baseline.json --base-model Qwen/Qwen2.5-7B-Instruct --dataset-version "primus-instruct@v1+hh-rlhf-harmless-base@v1" --method qlora+dpo

The final step prints the ship/retire decision and writes a model card + registry entry.

Before spending real GPU hours, validate the flow cheaply and offline first:

    !cd dula && PYTHONPATH=ml python -m dula_train.train_qlora --smoke
    !cd dula && PYTHONPATH=ml python -m dula_train.train_dpo --smoke

Kaggle's ~9-12h per-session cap matters here: a 7B QLoRA epoch over Primus plus the DPO pass may
not fit one session comfortably. If it doesn't, split the run across sessions -- ``train_qlora``
and ``train_dpo`` write to disk (``out/dula-qlora``, then ``out/dula-qlora-dpo``) and can be
resumed as separate Kaggle sessions within the same week's quota; keep the intermediate
``out/dula-qlora`` directory (e.g. commit it to a Kaggle Dataset) between sessions.
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
