"""Training/eval configuration (docs/08-AI/FineTuningStrategy.md, ModelSelection.md).

Defaults target a permissive base (Qwen2.5, ADR-0007) with QLoRA so a 3B–7B model fits a free
T4/L4. ``smoke`` swaps to a tiny random model for a CPU pipeline check (used to validate the
flow without a GPU).
"""

from __future__ import annotations

from pydantic import BaseModel


class TrainConfig(BaseModel):
    # Base model — permissive (Qwen/Mistral) per ADR-0007. Never Llama for the core. Bumped to
    # 7B for the third candidate: the first two runs (0.5B, 3B) both regressed safety_refusal_rate
    # vs their own untuned base regardless of size, so the fix is DPOConfig below, not size.
    base_model: str = "Qwen/Qwen2.5-7B-Instruct"
    # QLoRA / LoRA hyperparameters.
    load_in_4bit: bool = True
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    # Data + run.
    train_file: str = "data/train.jsonl"
    val_file: str = "data/val.jsonl"
    output_dir: str = "out/dula-qlora"
    # 1024 + gradient checkpointing keeps a 7B nf4 run inside a single 16 GB T4.
    max_seq_len: int = 1024
    epochs: float = 1.0
    max_steps: int = -1  # -1 = full epochs
    learning_rate: float = 2e-4
    batch_size: int = 2
    grad_accum: int = 8
    gradient_checkpointing: bool = True
    seed: int = 42
    # MLflow experiment (ADR-0010).
    mlflow_experiment: str = "dula-ai-sft"

    @classmethod
    def smoke(cls) -> TrainConfig:
        """A tiny, CPU-runnable config to validate the pipeline end-to-end without a GPU."""
        return cls(
            base_model="hf-internal-testing/tiny-random-LlamaForCausalLM",
            load_in_4bit=False,
            train_file="data/smoke.jsonl",
            val_file="data/smoke.jsonl",
            output_dir="out/smoke",
            max_seq_len=128,
            max_steps=1,
            batch_size=1,
            grad_accum=1,
        )


class DatasetConfig(BaseModel):
    # Primus (ODC-BY/MIT) instruction/reasoning sets. The canonical repos are gated (accept
    # terms once on HF, then use your token); the trend-cybertron mirrors are ungated but empty.
    instruct_dataset: str = "trendmicro-ailab/Primus-Instruct"
    reasoning_dataset: str | None = "trendmicro-ailab/Primus-Reasoning"
    license: str = "ODC-BY / MIT"
    val_fraction: float = 0.05
    seed: int = 42
    out_dir: str = "data"
    # The held-out benchmark used for the contamination check.
    benchmark_file: str = "evaluation/benchmark_seed.json"


class PreferenceDatasetConfig(BaseModel):
    """hh-rlhf harmless-base (MIT) -- DPO safety-restoration data.

    Anthropic's human-labelled harmlessness-preference pairs: ``chosen`` is the response human
    raters preferred on safety grounds, ``rejected`` the less-safe alternative. License verified
    MIT via the HF Hub API (2026-08-30), same gate discipline as Primus (ADR-0007).
    """

    dataset_id: str = "Anthropic/hh-rlhf"
    data_dir: str = "harmless-base"
    license: str = "MIT"
    val_fraction: float = 0.05
    seed: int = 42
    out_dir: str = "data"
    benchmark_file: str = "evaluation/benchmark_seed.json"
    # Keep only what the DPO pass will consume (see DPOConfig.max_steps); tokenizing all 42k
    # pairs cost minutes per run for nothing.
    max_pairs: int = 2_400


class DPOConfig(BaseModel):
    """Safety-restoration pass: a short DPO run over the just-trained SFT output.

    Targets the regression seen in both prior candidates (registry: 0.5B and 3B runs each
    regressed safety_refusal_rate vs their own untuned base) rather than model capacity.
    ``peft_config`` on the trainer means no separate reference model is materialized -- the
    same base with adapters disabled serves as the reference, matching standard trl practice.
    """

    base_model: str = "out/dula-qlora"  # the SFT output this pass further tunes
    train_file: str = "data/pref_train.jsonl"
    val_file: str = "data/pref_val.jsonl"
    output_dir: str = "out/dula-qlora-dpo"
    beta: float = 0.1
    # 512 total / 384 prompt (keep_end) fits chosen+rejected+reference passes on a 16 GB T4.
    max_seq_len: int = 512
    max_prompt_len: int = 384
    epochs: float = 1.0
    # harmless-base is ~42k pairs; a full epoch of 7B DPO on a T4 would blow Kaggle's 12h
    # session cap. 120 steps x 16 = 1,920 pairs is enough for a restoration pass.
    max_steps: int = 120
    learning_rate: float = 5e-6
    # DPO forwards chosen + rejected (and the reference) per example: micro-batch 1 on a T4,
    # same effective batch of 16 as SFT.
    batch_size: int = 1
    grad_accum: int = 16
    gradient_checkpointing: bool = True
    seed: int = 42
    mlflow_experiment: str = "dula-ai-dpo"

    @classmethod
    def smoke(cls) -> DPOConfig:
        """A tiny, CPU-runnable config to validate the DPO flow without a GPU."""
        return cls(
            base_model="hf-internal-testing/tiny-random-LlamaForCausalLM",
            train_file="data/pref_smoke.jsonl",
            val_file="data/pref_smoke.jsonl",
            output_dir="out/smoke-dpo",
            max_seq_len=128,
            max_steps=1,
            batch_size=1,
            grad_accum=1,
        )


class EvalConfig(BaseModel):
    # Either a local model dir/HF id, or an OpenAI-compatible endpoint (vLLM/llama.cpp/hosted).
    model: str = "out/dula-qlora-dpo"
    endpoint: str | None = None  # e.g. http://localhost:8000/v1 ; if set, uses the API path
    api_model_name: str = "dula-ai"
    benchmark_file: str = "evaluation/benchmark_seed.json"
    report_out: str = "out/eval_report.json"
    label: str = "candidate"
    max_new_tokens: int = 64
