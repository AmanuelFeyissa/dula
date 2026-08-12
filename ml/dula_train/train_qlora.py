"""QLoRA supervised fine-tuning (docs/08-AI/FineTuningStrategy.md, 09-MLOps/TrainingPipelines.md).

Fine-tunes a permissive base (Qwen2.5, ADR-0007) with QLoRA using trl's SFTTrainer, logging to
MLflow (ADR-0010). Produces a LoRA adapter + tokenizer in ``output_dir``. Run on a free GPU
(Kaggle/Lightning/Modal/Colab); ``--smoke`` runs one CPU step on a tiny model to validate flow.
Library versions move fast — pin via ``ml/requirements.txt`` and adjust arg names if needed.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from dula_train.config import TrainConfig


def train(cfg: TrainConfig) -> str:
    import mlflow
    import torch
    from datasets import load_dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import SFTConfig, SFTTrainer

    tokenizer = AutoTokenizer.from_pretrained(cfg.base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    # Fallback chat template for bases without one (e.g. the tiny smoke model), so trl can
    # render conversational "messages" rows.
    if tokenizer.chat_template is None:
        tokenizer.chat_template = (
            "{% for m in messages %}<|{{ m['role'] }}|>\n{{ m['content'] }}\n{% endfor %}"
            "{% if add_generation_prompt %}<|assistant|>\n{% endif %}"
        )

    cuda = torch.cuda.is_available()
    bf16 = cuda and torch.cuda.is_bf16_supported()  # Ampere+ (A100/L4); False on Kaggle T4
    compute_dtype = torch.bfloat16 if bf16 else torch.float16

    quant = None
    if cfg.load_in_4bit:
        quant = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_use_double_quant=True,
        )
    model = AutoModelForCausalLM.from_pretrained(
        cfg.base_model, quantization_config=quant, device_map="auto"
    )

    peft_config = LoraConfig(
        r=cfg.lora_r,
        lora_alpha=cfg.lora_alpha,
        lora_dropout=cfg.lora_dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules="all-linear",
    )

    train_ds = load_dataset("json", data_files=cfg.train_file, split="train")
    eval_ds = load_dataset("json", data_files=cfg.val_file, split="train")

    import inspect

    sft_kwargs: dict[str, object] = {
        "output_dir": cfg.output_dir,
        "num_train_epochs": cfg.epochs,
        "max_steps": cfg.max_steps,
        "per_device_train_batch_size": cfg.batch_size,
        "gradient_accumulation_steps": cfg.grad_accum,
        "learning_rate": cfg.learning_rate,
        "logging_steps": 1,
        "save_strategy": "no",
        "seed": cfg.seed,
        "report_to": [],
        "use_cpu": not cuda,
        "bf16": bf16,
        "fp16": cuda and not bf16,
    }
    # trl renamed the sequence-length arg across versions (max_seq_length -> max_length).
    sft_params = inspect.signature(SFTConfig.__init__).parameters
    if "max_seq_length" in sft_params:
        sft_kwargs["max_seq_length"] = cfg.max_seq_len
    elif "max_length" in sft_params:
        sft_kwargs["max_length"] = cfg.max_seq_len
    sft = SFTConfig(**sft_kwargs)

    mlflow.set_experiment(cfg.mlflow_experiment)
    with mlflow.start_run():
        mlflow.log_params(cfg.model_dump())
        trainer = SFTTrainer(
            model=model,
            args=sft,
            train_dataset=train_ds,
            eval_dataset=eval_ds,
            peft_config=peft_config,
            processing_class=tokenizer,
        )
        trainer.train()
        # Save a full, self-contained model when possible (merge LoRA into the base) so the
        # evaluator/serving can load it directly. Merging isn't supported on a 4-bit base, so
        # fall back to saving just the adapter there.
        try:
            merged = trainer.model.merge_and_unload()
            merged.save_pretrained(cfg.output_dir)
        except Exception:
            trainer.save_model(cfg.output_dir)
        tokenizer.save_pretrained(cfg.output_dir)
        mlflow.log_artifacts(cfg.output_dir, artifact_path="model")

    print(json.dumps({"output_dir": cfg.output_dir, "base_model": cfg.base_model}))
    return cfg.output_dir


def _write_smoke_data(path: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "messages": [
                {"role": "user", "content": "What mitigates brute force?"},
                {"role": "assistant", "content": "MFA and account lockout."},
            ]
        }
    ] * 4
    with p.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="QLoRA SFT for Dula AI.")
    parser.add_argument(
        "--smoke", action="store_true", help="1-step CPU flow check on a tiny model"
    )
    args = parser.parse_args()
    if args.smoke:
        cfg = TrainConfig.smoke()
        _write_smoke_data(cfg.train_file)
    else:
        cfg = TrainConfig()
    train(cfg)


if __name__ == "__main__":
    main()
