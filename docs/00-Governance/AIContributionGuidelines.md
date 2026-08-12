---
title: AI Contribution Guidelines
document_id: GOV-006
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Engineering Governance
audience: All contributors using AI assistance
phase: Documentation Bootstrap (M000)
related:
  - ./RepositoryGovernance.md
  - ./DocumentationStandards.md
  - ../10-Security/SecureDevelopment.md
---

# AI Contribution Guidelines

> **Purpose.** Define how AI-assisted code and documentation may be produced and must be
> validated, so that AI accelerates the project without introducing hallucinated facts,
> insecure code, or untraceable decisions. This document also governs how *this* bootstrap
> was produced.

## 1. Principles

1. **Human accountability.** A human contributor is responsible for every merged change,
   regardless of how much was AI-generated. "The AI wrote it" is never an excuse.
2. **AI as accelerator, not authority.** AI output is a draft to be verified against
   authoritative sources, never a source of truth.
3. **Traceability.** AI-assisted contributions are disclosed so reviewers can calibrate
   scrutiny.
4. **Security first.** AI-generated code is treated as untrusted until reviewed against
   [../10-Security/SecureDevelopment.md](../10-Security/SecureDevelopment.md).

## 2. Allowed Uses

- Drafting code, tests, and documentation.
- Refactoring, boilerplate, and repetitive transformations.
- Explaining code, generating review checklists, proposing designs.
- Generating candidate ADRs (which still require human decision and sign-off).

## 3. Disclosure & Attribution

- Commits with substantial AI assistance include a co-author trailer:
  `Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>` (or the relevant model).
- PR descriptions note where AI was materially used.
- AI-generated documentation is still subject to the human review in
  [DocumentationStandards.md](./DocumentationStandards.md).

## 4. Mandatory Human Validation

Before merge, a human must:

- **Verify facts.** Any factual claim about external systems, standards (MITRE ATT&CK,
  CVE, STIX, etc.), APIs, or libraries must be checked against primary sources. Unverified
  claims are marked **REQUIRES RESEARCH**, not asserted.
- **Verify code.** Read and understand AI-generated code; confirm it compiles, passes
  tests, and does what the PR claims.
- **Verify security.** Check for injection, secret leakage, unsafe deserialization,
  SSRF, and unsafe tool execution.
- **Verify licensing.** Ensure AI-suggested dependencies and datasets are license-clean
  (see [../08-AI/DatasetStrategy.md](../08-AI/DatasetStrategy.md)).

## 5. Hallucination Prevention

- Prefer retrieval over recall: ground AI on repository docs and primary sources.
- Do not let AI invent library APIs, config keys, CLI flags, or standard identifiers —
  cross-check against real documentation.
- When the AI is uncertain or the fact is unverifiable in-session, the output must say so
  explicitly rather than fabricate.
- Numbers (benchmarks, hardware sizing, costs) produced by AI are estimates and labeled
  as such until measured.

## 6. AI in the Product vs AI in Development

This document governs AI used **to build** Dula. AI used **inside** Dula (agents, RAG,
Dula AI) is governed separately by:

- [../10-Security/AIThreatModel.md](../10-Security/AIThreatModel.md)
- [../13-Agents/README.md](../13-Agents/README.md)
- [../08-AI/EvaluationStrategy.md](../08-AI/EvaluationStrategy.md)

The two must not be conflated. Guardrails on the product are not satisfied by these
development guidelines, and vice versa.

## 7. Reproducibility

- Prompts/config that generate committed artifacts (e.g. scaffolding, dataset transforms)
  should themselves be committed where practical.
- Model-generated data used for training or evaluation must record the generating model,
  version, prompt, and date (see [../09-MLOps/DatasetVersioning.md](../09-MLOps/DatasetVersioning.md)).

## 8. This Bootstrap

This documentation set was generated with AI assistance during the Documentation
Bootstrap phase (M000). Per these guidelines, it is **Draft** status: technology
recommendations, sizing, and external-standard references are **candidates requiring
human verification and ADR sign-off** before implementation. Items the AI could not
verify in-session are explicitly tagged **REQUIRES RESEARCH** / **REQUIRES DECISION**.

## Related Documents

- [./RepositoryGovernance.md](./RepositoryGovernance.md)
- [../10-Security/AIThreatModel.md](../10-Security/AIThreatModel.md)
