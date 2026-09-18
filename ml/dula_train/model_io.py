"""Load a causal LM from an HF id, a full model directory, or a PEFT adapter-only directory.

A 4-bit QLoRA run can't merge its adapter into the quantized base, so ``train_qlora`` /
``train_dpo`` save adapter-only directories (``adapter_config.json`` + weights). Every later
stage -- the DPO pass, the evaluator -- must then load the base named in the adapter config and
apply the adapter on top, rather than calling ``from_pretrained`` on the directory directly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def adapter_base_model(path: str) -> str | None:
    """The base model an adapter-only directory was trained on, or None for a full model."""
    cfg = Path(path) / "adapter_config.json"
    if not cfg.is_file():
        return None
    return str(json.loads(cfg.read_text(encoding="utf-8"))["base_model_name_or_path"])


def quant_config(*, enabled: bool) -> Any | None:
    """nf4 4-bit config on CUDA (fp16 compute on T4, bf16 on Ampere+); None on CPU."""
    import torch
    from transformers import BitsAndBytesConfig

    if not (enabled and torch.cuda.is_available()):
        return None
    bf16 = torch.cuda.is_bf16_supported()
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16 if bf16 else torch.float16,
        bnb_4bit_use_double_quant=True,
    )


def load_causal_lm(path: str, *, quant: Any | None, trainable_adapter: bool = False) -> Any:
    """Load ``path`` (HF id, full model dir, or adapter dir) as a ready-to-use causal LM."""
    import torch
    from transformers import AutoModelForCausalLM

    base = adapter_base_model(path)
    kwargs: dict[str, Any] = {"quantization_config": quant}
    if torch.cuda.is_available():
        kwargs["device_map"] = "auto"
        if quant is None:
            kwargs["torch_dtype"] = torch.float16
    model = AutoModelForCausalLM.from_pretrained(base or path, **kwargs)
    if base is None:
        return model

    from peft import PeftModel, prepare_model_for_kbit_training

    if quant is not None and trainable_adapter:
        model = prepare_model_for_kbit_training(model)
    return PeftModel.from_pretrained(model, path, is_trainable=trainable_adapter)
