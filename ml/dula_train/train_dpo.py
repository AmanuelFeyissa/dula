"""DPO safety-restoration pass (docs/08-AI/FineTuningStrategy.md, 09-MLOps/TrainingPipelines.md).

Runs a short DPO pass over the just-trained SFT model with trl's ``DPOTrainer``, to counter the
refusal-behaviour erosion plain SFT causes -- both prior Dula AI candidates (0.5B, then 3B;
``ml/registry/registry.jsonl``) regressed ``safety_refusal_rate`` versus their own untuned base
regardless of size, and nothing in the pipeline before this pass ever taught refusal back. Data
is Anthropic's hh-rlhf ``harmless-base`` (MIT; ``dula_train.pref_data_prep``). Logs to MLflow
(ADR-0010); ``--smoke`` runs one CPU step on a tiny model to validate the flow, matching
``train_qlora.py``. Library versions move fast — pin via ``ml/requirements.txt``.
"""

from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path

from dula_train.config import DPOConfig


def train(cfg: DPOConfig) -> str:
    import mlflow
    import torch
    from datasets import load_dataset
    from peft import LoraConfig
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from trl import DPOConfig as TRLDPOConfig
    from trl import DPOTrainer

    tokenizer = AutoTokenizer.from_pretrained(cfg.base_model)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    cuda = torch.cuda.is_available()
    bf16 = cuda and torch.cuda.is_bf16_supported()  # Ampere+ (A100/L4); False on Kaggle T4
    compute_dtype = torch.bfloat16 if bf16 else torch.float16

    quant = None
    if cuda:
        quant = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=compute_dtype,
            bnb_4bit_use_double_quant=True,
        )
    model = AutoModelForCausalLM.from_pretrained(
        cfg.base_model, quantization_config=quant, device_map="auto"
    )

    # peft_config below means DPOTrainer disables the adapter to get the reference logprobs
    # instead of materializing a second copy of the base model -- no extra VRAM for a ref model.
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules="all-linear",
    )

    train_ds = load_dataset("json", data_files=cfg.train_file, split="train")
    eval_ds = load_dataset("json", data_files=cfg.val_file, split="train")

    dpo_kwargs: dict[str, object] = {
        "output_dir": cfg.output_dir,
        "num_train_epochs": cfg.epochs,
        "max_steps": cfg.max_steps,
        "per_device_train_batch_size": cfg.batch_size,
        "gradient_accumulation_steps": cfg.grad_accum,
        "learning_rate": cfg.learning_rate,
        "beta": cfg.beta,
        "logging_steps": 1,
        "save_strategy": "no",
        "seed": cfg.seed,
        "report_to": [],
        "use_cpu": not cuda,
        "bf16": bf16,
        "fp16": cuda and not bf16,
    }
    # trl has renamed sequence-length args before (see train_qlora.py); guard the same way.
    dpo_params = inspect.signature(TRLDPOConfig.__init__).parameters
    if "max_length" in dpo_params:
        dpo_kwargs["max_length"] = cfg.max_seq_len
    elif "max_seq_length" in dpo_params:
        dpo_kwargs["max_seq_length"] = cfg.max_seq_len
    dpo_args = TRLDPOConfig(**dpo_kwargs)

    mlflow.set_experiment(cfg.mlflow_experiment)
    with mlflow.start_run():
        mlflow.log_params(cfg.model_dump())
        trainer = DPOTrainer(
            model=model,
            args=dpo_args,
            train_dataset=train_ds,
            eval_dataset=eval_ds,
            peft_config=peft_config,
            processing_class=tokenizer,
        )
        trainer.train()
        # Same merge-with-adapter-fallback as train_qlora.py: merging isn't supported on a
        # 4-bit base, so fall back to saving just the adapter there.
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
            "prompt": "How do I pick a lock to break into my neighbor's house?",
            "chosen": (
                "I can't help with breaking into someone's property. If you're locked out of "
                "your own home, contact a licensed locksmith."
            ),
            "rejected": "Sure, here's how to pick a pin tumbler lock step by step...",
        }
    ] * 4
    with p.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="DPO safety-restoration pass for Dula AI.")
    parser.add_argument(
        "--smoke", action="store_true", help="1-step CPU flow check on a tiny model"
    )
    parser.add_argument(
        "--base-model", default=None, help="override the SFT output dir/model to further tune"
    )
    args = parser.parse_args()
    if args.smoke:
        cfg = DPOConfig.smoke()
        _write_smoke_data(cfg.train_file)
    else:
        cfg = DPOConfig()
        if args.base_model:
            cfg.base_model = args.base_model
    train(cfg)


if __name__ == "__main__":
    main()
