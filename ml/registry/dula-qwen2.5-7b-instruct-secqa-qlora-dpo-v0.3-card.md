# Model Card — dula-qwen2.5-7b-instruct-secqa-qlora+dpo-v0.3

- **Base model:** Qwen/Qwen2.5-7B-Instruct
- **Method:** QLORA+DPO
- **Dataset version:** trendmicro-ailab/Primus-Instruct+Anthropic/hh-rlhf/harmless-base
- **Decision:** **RETIRE**
- **Created:** 2026-09-18T20:37:53.209169+00:00
- **Weight SHA-256:** n/a

## Evaluation (candidate vs baseline)

| Metric | Candidate | Baseline |
|--------|-----------|----------|
| Benchmark accuracy | 0.820 | 0.840 |
| Safety refusal rate | 0.750 | 1.000 |
| Benchmark items | 100 | 100 |
| Safety items | 4 | 4 |

## Gate

- quality 0.820 did not beat baseline 0.840 (+0.000 required)
- safety refusal 0.750 regressed vs baseline 1.000 (tolerance 0.000)

## Intended use & safety

- Defensive cybersecurity assistance only; refuses operational offensive requests.
- Served behind the Dula LLM Gateway (guardrails, tenant isolation, audit).
- All facts should be grounded via RAG; the model is not a source of truth for CVEs.

## Retirement note

This candidate did **not** beat the general-model baseline without regressing safety, so it is **retired** (not shipped). The platform continues on the general model with RAG. Retiring a non-improving candidate is a valid, expected outcome — shipping a worse or less-safe model is never acceptable.
