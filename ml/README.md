# ml/ — Dula AI (Product 2): training, evaluation, serving

Standalone GPU project for training and evaluating **Dula AI** (Product 2). It is **not** part
of the `uv` workspace — the heavy libraries (torch/transformers/peft/trl) install only here, on
an **external free GPU** (the local dev machine has no GPU). The quality- and safety-critical
logic (dataset formatting, dedup, contamination checks, evaluation scoring, ship/retire gate,
registry, model card) lives in the torch-free, CI-tested package **`packages/dula-ml`**, which
this project imports — so the rules on the GPU runner match CI exactly.

See [../docs/08-AI/README.md](../docs/08-AI/README.md), [../docs/09-MLOps/README.md](../docs/09-MLOps/README.md),
and [../docs/08-AI/FineTuningStrategy.md](../docs/08-AI/FineTuningStrategy.md).

## Layout

- `dula_train/` — runner code: `config.py`, `data_prep.py`, `train_qlora.py`, `eval_runner.py`,
  `decide.py`.
- `evaluation/benchmark_seed.json` — illustrative held-out security benchmark (MCQ + safety).
  Replace/extend with a real suite (CyberMetric/SecEval/CTIBench) for meaningful numbers.
- `runners/` — `modal_train.py` (Modal), `kaggle_qlora.py` (Kaggle/Colab/Lightning).
- `requirements.txt` — the GPU environment (pin per run for reproducibility).
- `datasets/`, `serving/` — dataset build configs (DVC-tracked) and serving packaging (grows
  in later phases).

## Base model & datasets

- Base: permissive **Qwen2.5 / Mistral** (ADR-0007) — never Llama for the core.
- Data: **Primus** (Trend Micro; ODC-BY/MIT) instruction + reasoning sets, plus RAG public
  sources for retrieval. See [../docs/08-AI/KnowledgeSources.md](../docs/08-AI/KnowledgeSources.md).

## Run (free GPU)

```bash
pip install -r ml/requirements.txt && pip install -e packages/dula-ml
huggingface-cli login                      # only if datasets/models are gated
python -m dula_train.data_prep --out ml/data
PYTHONPATH=ml python -m dula_train.train_qlora
PYTHONPATH=ml python -m dula_train.eval_runner --model out/dula-qlora    --label candidate --out out/candidate.json
PYTHONPATH=ml python -m dula_train.eval_runner --model Qwen/Qwen2.5-3B-Instruct --label baseline --out out/baseline.json
PYTHONPATH=ml python -m dula_train.decide --candidate out/candidate.json --baseline out/baseline.json
```

- **Kaggle** (~30 GPU hrs/week) — paste `runners/kaggle_qlora.py` header steps into a GPU notebook.
- **Lightning AI** (~80 GPU hrs/month) — run the same steps in a Studio.
- **Modal** ($30/month) — `modal run ml/runners/modal_train.py` for reproducible scripted runs.

`decide.py` prints **ship** or **retire** and writes a model card + registry entry. A run
completes either way — a candidate that does not beat the general model without regressing
safety is **retired**, and the platform stays on the general model + RAG. **Shipping a worse
model is never acceptable.** (Phase 04's first candidate and Phase 10/M011's second candidate
were both retired for exactly this reason — see `ml/registry/registry.jsonl`.)

Once a candidate ships, promote it through the lifecycle stages and manage rollback via
`ml/dula_train/promote.py` (docs/09-MLOps/ModelLifecycle.md, `dula_ml.lifecycle`).

## Flow check without a GPU

`PYTHONPATH=ml python -m dula_train.train_qlora --smoke` runs one CPU step on a tiny model to
validate the flow (requires the `requirements.txt` env). The torch-free logic is covered by
`packages/dula-ml` tests in CI.

## Serving the result

A shipped adapter is merged/quantized and served behind the **LLM Gateway** via an
OpenAI-compatible endpoint (vLLM / llama.cpp) — set `provider=openai` on `apps/ai-gateway`
(see [../docs/12-API/AIGatewayAPI.md](../docs/12-API/AIGatewayAPI.md)). No app code changes.
