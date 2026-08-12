"""Training/eval configuration (docs/08-AI/FineTuningStrategy.md, ModelSelection.md).

Defaults target a permissive base (Qwen2.5, ADR-0007) with QLoRA so a 3B–7B model fits a free
T4/L4. ``smoke`` swaps to a tiny random model for a CPU pipeline check (used to validate the
flow without a GPU).
"""

from __future__ import annotations

from pydantic import BaseModel


class TrainConfig(BaseModel):
    # Base model — permissive (Qwen/Mistral) per ADR-0007. Never Llama for the core.
    base_model: str = "Qwen/Qwen2.5-3B-Instruct"
    # QLoRA / LoRA hyperparameters.
    load_in_4bit: bool = True
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    # Data + run.
    train_file: str = "data/train.jsonl"
    val_file: str = "data/val.jsonl"
    output_dir: str = "out/dula-qlora"
    max_seq_len: int = 2048
    epochs: float = 1.0
    max_steps: int = -1  # -1 = full epochs
    learning_rate: float = 2e-4
    batch_size: int = 2
    grad_accum: int = 8
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


class EvalConfig(BaseModel):
    # Either a local model dir/HF id, or an OpenAI-compatible endpoint (vLLM/llama.cpp/hosted).
    model: str = "out/dula-qlora"
    endpoint: str | None = None  # e.g. http://localhost:8000/v1 ; if set, uses the API path
    api_model_name: str = "dula-ai"
    benchmark_file: str = "evaluation/benchmark_seed.json"
    report_out: str = "out/eval_report.json"
    label: str = "candidate"
    max_new_tokens: int = 64
