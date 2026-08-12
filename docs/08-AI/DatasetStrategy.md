---
title: Dataset Strategy
document_id: AI-005
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: AI / Data
audience: AI/ML & data engineers, legal liaison
phase: Documentation Bootstrap (M000)
related:
  - ./DataPipeline.md
  - ../09-MLOps/DatasetVersioning.md
  - ../01-Project/Dependencies.md
---

# Dataset Strategy

> **Purpose.** Define what data trains/evaluates Dula AI and grounds RAG, sourced only from
> **legitimate, licensed** origins with clear provenance. We do **not** recommend or use
> illegally acquired data.

## 1. Legitimate Sources

| Source | Use | Licensing note (REQUIRES RESEARCH per source) |
|--------|-----|-----------------------------------------------|
| MITRE ATT&CK | TTP knowledge, mapping | Check MITRE terms/attribution |
| CVE / NVD | Vulnerability data | Public; verify usage terms |
| CISA advisories | Advisories/KEV | Public gov; verify |
| CAPEC | Attack patterns | MITRE terms |
| Sigma rules | Detection engineering | Repo license (often permissive) |
| YARA rules | Malware ID | Per-rule/repo license |
| STIX/TAXII feeds | Threat intel structure/content | Feed-specific terms |
| Public security research/blogs/docs | Reasoning, explanations | Copyright — respect licenses/robots; prefer permissive/open |
| Sanitized security telemetry | Realistic examples | Must be de-identified & consented |
| Synthetic datasets | Fill gaps, instruction data | Record generator/prompt |

> **Every source's license is verified individually before use.** Non-commercial or
> restrictive licenses are quarantined to internal research and never shipped in the
> product ([../01-Project/Dependencies.md](../01-Project/Dependencies.md)).

## 2. Data Governance

- **Provenance:** every dataset records source, license, acquisition date, and method.
- **Privacy:** no PII/customer-identifying data in training sets; sanitize/de-identify
  telemetry ([../10-Security/DataSecurity.md](../10-Security/DataSecurity.md)).
- **Quality:** cleaning, normalization, and **deduplication** (near-dup detection) before
  use.
- **Versioning:** immutable, hash-addressed dataset versions
  ([../09-MLOps/DatasetVersioning.md](../09-MLOps/DatasetVersioning.md)).
- **Splits:** train/validation/test + a held-out **eval/benchmark** set never used in
  training (prevents leakage).

## 3. Annotation

- Where labels are needed (e.g. task datasets), define annotation guidelines, reviewer
  agreement checks, and store annotator provenance. Prefer expert review for security
  correctness.

## 4. Synthetic Data

- Model-generated instruction/eval data is allowed but labeled synthetic, with generator,
  version, and prompt recorded; validated by humans for correctness before training use.
- Guard against benchmark contamination (synthetic gen must not see the eval set).

## 5. Contamination & Leakage Controls

- The benchmark/eval set is isolated; training pipelines assert no overlap with eval via
  hashing. See [./Benchmarking.md](./Benchmarking.md).

## 6. Safety

- Exclude operational offensive content that would degrade safety alignment; retain enough
  defensive/analytical context for legitimate tasks (see
  [../02-Vision/GuidingPrinciples.md](../02-Vision/GuidingPrinciples.md)).

## Related Documents

- [./DataPipeline.md](./DataPipeline.md) · [../09-MLOps/DatasetVersioning.md](../09-MLOps/DatasetVersioning.md)
