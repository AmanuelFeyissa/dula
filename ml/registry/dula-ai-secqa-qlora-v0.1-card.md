# Model Card — dula-qwen2.5-0.5b-instruct-secqa-qlora-v0.1

- **Base model:** Qwen/Qwen2.5-0.5B-Instruct
- **Method:** QLORA
- **Dataset version:** trendmicro-ailab/Primus-Instruct
- **Decision:** **RETIRE**
- **Created:** 2026-08-12T12:56:24.920893+00:00
- **Weight SHA-256:** n/a

## Evaluation (candidate vs baseline)

| Metric | Candidate | Baseline |
|--------|-----------|----------|
| Benchmark accuracy | 0.360 | 0.370 |
| Safety refusal rate | 0.250 | 0.500 |
| Benchmark items | 100 | 100 |
| Safety items | 4 | 4 |

## Gate

- quality 0.360 did not beat baseline 0.370 (+0.000 required)
- safety refusal 0.250 regressed vs baseline 0.500 (tolerance 0.000)

## Intended use & safety

- Defensive cybersecurity assistance only; refuses operational offensive requests.
- Served behind the Dula LLM Gateway (guardrails, tenant isolation, audit).
- All facts should be grounded via RAG; the model is not a source of truth for CVEs.

## Retirement note

This candidate did **not** beat the general-model baseline without regressing safety, so it is **retired** (not shipped). The platform continues on the general model with RAG. Retiring a non-improving candidate is a valid Phase 04 outcome.
