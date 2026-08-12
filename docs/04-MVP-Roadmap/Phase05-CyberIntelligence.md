---
title: Phase 05 — Cyber Intelligence
document_id: MVP-005
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: AI / Backend
audience: All contributors
phase: Documentation Bootstrap (M000)
related:
  - ../02-Vision/UseCases.md
  - ../08-AI/RAGEngineering.md
---

# Phase 05 — Cyber Intelligence

> **Purpose.** Expand domain capabilities: CTI extraction, vulnerability analysis, and
> detection-engineering assistance, leveraging Dula AI + RAG.

## Objective
Deliver UC-05 (CTI extraction/summarization), UC-07 (vuln analysis), and UC-04 (detection
authoring assist for Sigma/YARA).

## Scope
- CTI: advisory summarization, IOC/TTP extraction, STIX mapping
  ([../07-Database/DataModel.md](../07-Database/DataModel.md)).
- Vulnerability reasoning: CVE context + prioritization guidance.
- Detection authoring: draft/tune Sigma & YARA; coverage vs ATT&CK.
- Domain-specific benchmark suites added ([../08-AI/Benchmarking.md](../08-AI/Benchmarking.md)).

## Dependencies
- Phase 04 (Dula AI) and Phase 03 (RAG) complete.

## Deliverables
- Working CTI/vuln/detection assist features with grounded, cited outputs and structured
  extraction.

## Implementation Requirements
- Structured output validation (extraction schemas, rule syntax checks)
  ([../12-API/APIStandards.md](../12-API/APIStandards.md)).

## Tests
- Benchmark suites for CTI extraction and detection authoring; correctness of rule syntax;
  UC E2E ([../15-Testing/AIEvaluation.md](../15-Testing/AIEvaluation.md)).

## Security Requirements
- Untrusted-source handling for ingested advisories; dual-use safety on detection/analysis
  outputs ([../10-Security/AIThreatModel.md](../10-Security/AIThreatModel.md)).

## Documentation
- Feature docs + benchmark additions; update PROJECT_STATE.

## Acceptance Criteria
- Extraction/authoring meet benchmark thresholds; generated rules are syntactically valid
  and reviewable.

## Definition of Done
- Global DoD + above.
