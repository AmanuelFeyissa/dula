# ADR-0005: Model Serving Runtime

- Status: Accepted
- Date: 2026-08-11
- Deciders: AI, Platform
- Related: [../08-AI/InferenceArchitecture.md](../08-AI/InferenceArchitecture.md)

## Context
Serving must span GPU (throughput) and CPU/air-gapped (low-resource), behind the LLM
gateway, with no external dependency.

## Options Considered
1. **vLLM** (GPU) + **llama.cpp/GGUF** (CPU/edge/air-gapped).
2. HF TGI — capable GPU server.
3. TensorRT-LLM — max GPU perf, NVIDIA-locked, complex.
4. Ollama — great DX (wraps llama.cpp), best for dev/small on-prem.

## Decision
- **vLLM for GPU serving; llama.cpp/GGUF for CPU/air-gapped; Ollama for local dev.**
- All runtimes sit **behind the LLM gateway**; callers never bind to a runtime.

## Consequences
- Covers high-throughput and offline/low-resource; quantized variants enable CPU serving.
- GPU availability in air-gapped installs remains a watchlist risk (mitigated by CPU path).

## Compliance / Verification
- No service calls a serving runtime directly; only via the gateway.
