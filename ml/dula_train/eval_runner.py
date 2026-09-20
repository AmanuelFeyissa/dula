"""Evaluation runner (docs/08-AI/EvaluationStrategy.md, 15-Testing/AIEvaluation.md).

Runs the benchmark (multiple-choice security QA) and a safety suite against a model — either a
local transformers checkpoint or an OpenAI-compatible endpoint (vLLM / llama.cpp server / hosted
served behind the gateway) — and writes an ``EvalReport`` (scored by the torch-free
``dula-ml`` logic). Run once per candidate and once for the baseline; ``decide.py`` compares them.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from dula_ml.evaluation import EvalReport, accuracy
from dula_ml.tasks import (
    RuleItem,
    TaskSuite,
    extract_iocs,
    extract_technique_ids,
    parse_safety,
    score_extraction,
    score_rules,
    score_safety,
    score_triage,
    sigma_errors,
    yara_errors,
)

from dula_train.config import EvalConfig

_MCQ_INSTRUCTION = "Answer with the single letter of the correct choice."
# A rule/extraction answer needs room for a whole detection; MCQ/safety do not.
_TASK_MAX_NEW_TOKENS = 512
_RULE_INSTRUCTION = {
    "sigma": "Write a single Sigma detection rule as YAML in one ```yaml code block.",
    "yara": "Write a single YARA rule in one ```yara code block.",
}


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
            from transformers import AutoTokenizer, pipeline

            from dula_train.model_io import load_causal_lm, quant_config

            # 4-bit on GPU so a 7B candidate *and* its baseline fit a free T4; on CPU (smoke)
            # the tiny model loads as-is. Both sides of the gate load the same way.
            model = load_causal_lm(cfg.model, quant=quant_config(enabled=True))
            tokenizer = AutoTokenizer.from_pretrained(cfg.model)
            self._pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)

    def generate(self, prompt: str, *, max_new_tokens: int | None = None) -> str:
        tokens = max_new_tokens or self._cfg.max_new_tokens
        if self._pipe is not None:
            # Apply the chat template so an instruct base answers a bare prompt properly
            # (the raw string alone yields autocomplete, not an answer/refusal).
            tok = self._pipe.tokenizer
            text = prompt
            if getattr(tok, "chat_template", None):
                text = tok.apply_chat_template(
                    [{"role": "user", "content": prompt}],
                    tokenize=False,
                    add_generation_prompt=True,
                )
            out = self._pipe(text, max_new_tokens=tokens, do_sample=False)
            return str(out[0]["generated_text"])[len(text) :]
        import httpx

        resp = httpx.post(
            f"{self._cfg.endpoint}/chat/completions",
            json={
                "model": self._cfg.api_model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": tokens,
                "temperature": 0.0,
            },
            timeout=120.0,
        )
        resp.raise_for_status()
        return str(resp.json()["choices"][0]["message"]["content"])


def _rule_prompt(kind: str, item: RuleItem) -> str:
    return f"{item.prompt}\n{_RULE_INSTRUCTION[kind]}"


def run(cfg: EvalConfig) -> EvalReport:
    from dula_ml.evaluation import MCQItem, TaskScore

    bench = json.loads(Path(cfg.benchmark_file).read_text(encoding="utf-8"))
    mcq = [MCQItem.model_validate(i) for i in bench.get("mcq", [])]
    safety_items = parse_safety(bench.get("safety", []))
    suite = TaskSuite.model_validate(bench.get("tasks", {}))

    # Opt-in raw-answer capture (DULA_EVAL_DUMP=path): lets us audit *why* a suite scored the
    # way it did (e.g. a validator rejecting well-formed rules) without a second GPU run.
    dump: dict[str, list[dict[str, str]]] = {}

    def gen(prompt: str, bucket: str, item_id: str, **kw: int) -> str:
        answer = backend.generate(prompt, **kw)
        dump.setdefault(bucket, []).append({"id": item_id, "prompt": prompt, "answer": answer})
        return answer

    backend = _Backend(cfg)
    mcq_answers = [gen(_format_mcq(i.model_dump()), "mcq", i.id) for i in mcq]
    safety_answers = [gen(i.prompt, "safety", i.id) for i in safety_items]
    refusal_rate, over_refusal = score_safety(safety_items, safety_answers)
    n_benign = sum(1 for i in safety_items if i.expect == "comply")

    tasks: dict[str, TaskScore] = {}
    validators = {"sigma": sigma_errors, "yara": yara_errors}
    for kind, items in (("sigma", suite.sigma), ("yara", suite.yara)):
        if items:
            answers = [
                gen(_rule_prompt(kind, it), kind, it.id, max_new_tokens=_TASK_MAX_NEW_TOKENS)
                for it in items
            ]
            tasks[kind] = score_rules(kind, items, answers, validators[kind])
    for name, items_ex, extractor in (
        ("ioc", suite.ioc, extract_iocs),
        ("attack", suite.attack, extract_technique_ids),
    ):
        if items_ex:
            answers = [
                gen(it.text, name, it.id, max_new_tokens=_TASK_MAX_NEW_TOKENS) for it in items_ex
            ]
            tasks[name] = score_extraction(name, items_ex, answers, extractor)
    if suite.triage:
        triage_answers = [gen(_format_mcq(i.model_dump()), "triage", i.id) for i in suite.triage]
        tasks["triage"] = score_triage(suite.triage, triage_answers)

    dump_path = os.environ.get("DULA_EVAL_DUMP")
    if dump_path:
        target = Path(dump_path)
        if target.is_dir() or not target.suffix:
            target = target / f"answers_{cfg.label}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(dump, indent=2), encoding="utf-8")

    report = EvalReport(
        model=cfg.label,
        accuracy=accuracy(mcq, mcq_answers),
        safety_refusal_rate=refusal_rate,
        n_items=len(mcq),
        n_safety=len(safety_items),
        over_refusal_rate=over_refusal,
        n_benign=n_benign,
        tasks=tasks,
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
