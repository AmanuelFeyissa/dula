# ADR-0007: Base Model Family for Dula AI

- Status: Accepted (family/licensing policy) — specific model per benchmark
- Date: 2026-08-11
- Deciders: AI, Legal liaison
- Related: [../08-AI/ModelSelection.md](../08-AI/ModelSelection.md)

## Context
Dula must ship (including air-gapped, commercial, redistributable). Base-model **license**
is therefore a hard gate before quality. Licensing verified via research (Aug 2026).

## Options Considered (licensing findings)
1. **Qwen** family — most releases under **Apache-2.0** (clean commercial/self-host/
   redistribution/fine-tune).
2. **Mistral** family — much of the lineup under **Apache-2.0**, standout for permissive terms.
3. **Llama** family — **Meta Community License**, *not* standard OSS: acceptable-use policy,
   derivative-naming requirement, a large-platform commercial threshold, and regional terms
   (e.g. EU multimodal restrictions).
4. Gemma/Phi — permissive options to keep on the shortlist.

## Decision
- **Prefer Apache-2.0 open-weight families (Qwen, Mistral) as the primary base-model
  candidates** because their licenses cleanly permit commercial use, self-hosting,
  air-gapped redistribution, and fine-tuning.
- **Deprioritize Llama for the core product** due to its custom Community License and
  regional restrictions; it may be used only where its terms are acceptable for a given
  deployment, never assumed license-clean.
- **The specific model + size is chosen empirically** by the internal benchmark
  ([../08-AI/Benchmarking.md](../08-AI/Benchmarking.md)); this ADR fixes the **licensing
  policy and candidate set**, not the final checkpoint.
- **Model-weight provenance/hashes must be verified** on ingestion (supply-chain, review S2).

## Consequences
- Air-gapped/commercial redistribution is legally clean by default; final model remains
  data-driven and swappable behind the gateway/registry.

## Compliance / Verification
- License gate blocks any model failing Apache-2.0-equivalent terms unless explicitly
  approved for a specific deployment; weight hashes verified on load.
