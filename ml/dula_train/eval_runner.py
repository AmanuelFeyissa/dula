"""Evaluation runner (docs/08-AI/EvaluationStrategy.md, 15-Testing/AIEvaluation.md).

Runs the benchmark (multiple-choice security QA) and a safety suite against a model — either a
local transformers checkpoint or an OpenAI-compatible endpoint (vLLM / llama.cpp server / hosted
served behind the gateway) — and writes an ``EvalReport`` (scored by the torch-free
``dula-ml`` logic). Run once per candidate and once for the baseline; ``decide.py`` compares them.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from dula_ml.evaluation import EvalReport, accuracy, safety_refusal_rate

from dula_train.config import EvalConfig

_MCQ_INSTRUCTION = "Answer with the single letter of the correct choice."


def _format_mcq(item: dict[str, object]) -> str:
    choices = item["choices"]
    assert isinstance(choices, list)
    lettered = "\n".join(f"{chr(65 + i)}. {c}" for i, c in enumerate(choices))
    return f"{item['question']}\n{lettered}\n{_MCQ_INSTRUCTION}"


class _Backend:
    """Either a local transformers model or an OpenAI-compatible endpoint."""

    def __init__(self, cfg: EvalConfig) -> None:
        self._cfg = cfg
        self._pipe = None
        if cfg.endpoint is None:
            from transformers import pipeline

            self._pipe = pipeline("text-generation", model=cfg.model)

    def generate(self, prompt: str) -> str:
        if self._pipe is not None:
            out = self._pipe(prompt, max_new_tokens=self._cfg.max_new_tokens, do_sample=False)
            return str(out[0]["generated_text"])[len(prompt) :]
        import httpx

        resp = httpx.post(
            f"{self._cfg.endpoint}/chat/completions",
            json={
                "model": self._cfg.api_model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": self._cfg.max_new_tokens,
                "temperature": 0.0,
            },
            timeout=120.0,
        )
        resp.raise_for_status()
        return str(resp.json()["choices"][0]["message"]["content"])


def run(cfg: EvalConfig) -> EvalReport:
    from dula_ml.evaluation import MCQItem

    bench = json.loads(Path(cfg.benchmark_file).read_text(encoding="utf-8"))
    mcq = [MCQItem.model_validate(i) for i in bench.get("mcq", [])]
    safety_prompts = list(bench.get("safety", []))

    backend = _Backend(cfg)
    mcq_answers = [backend.generate(_format_mcq(i.model_dump())) for i in mcq]
    safety_answers = [backend.generate(p) for p in safety_prompts]

    report = EvalReport(
        model=cfg.label,
        accuracy=accuracy(mcq, mcq_answers),
        safety_refusal_rate=safety_refusal_rate(safety_answers),
        n_items=len(mcq),
        n_safety=len(safety_answers),
    )
    Path(cfg.report_out).parent.mkdir(parents=True, exist_ok=True)
    Path(cfg.report_out).write_text(report.model_dump_json(indent=2), encoding="utf-8")
    print(report.model_dump_json())
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a model on the security benchmark.")
    parser.add_argument("--model", default=EvalConfig().model)
    parser.add_argument("--endpoint", default=None)
    parser.add_argument("--label", default="candidate")
    parser.add_argument("--benchmark", default=EvalConfig().benchmark_file)
    parser.add_argument("--out", default=EvalConfig().report_out)
    args = parser.parse_args()
    run(
        EvalConfig(
            model=args.model,
            endpoint=args.endpoint,
            label=args.label,
            benchmark_file=args.benchmark,
            report_out=args.out,
        )
    )


if __name__ == "__main__":
    main()
