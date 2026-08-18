# Model Card — dula-qwen2.5-3b-instruct-secqa-qlora-v0.2

- **Base model:** Qwen/Qwen2.5-3B-Instruct
- **Method:** QLORA
- **Dataset version:** trendmicro-ailab/Primus-Instruct
- **Decision:** **RETIRE**
- **Created:** 2026-08-18T08:18:26.137981+00:00
- **Weight SHA-256:** n/a

## Evaluation (candidate vs baseline)

| Metric | Candidate | Baseline |
|--------|-----------|----------|
| Benchmark accuracy | 0.620 | 0.600 |
| Safety refusal rate | 0.750 | 1.000 |
| Benchmark items | 100 | 100 |
| Safety items | 4 | 4 |

## Gate

- safety refusal 0.750 regressed vs baseline 1.000 (tolerance 0.000)

## Intended use & safety

- Defensive cybersecurity assistance only; refuses operational offensive requests.
- Served behind the Dula LLM Gateway (guardrails, tenant isolation, audit).
- All facts should be grounded via RAG; the model is not a source of truth for CVEs.

## Retirement note

This candidate did **not** beat the general-model baseline without regressing safety, so it is **retired** (not shipped). The platform continues on the general model with RAG. Retiring a non-improving candidate is a valid, expected outcome — shipping a worse or less-safe model is never acceptable.
