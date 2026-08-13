---
title: Phase 09 — Production (GA)
document_id: MVP-009
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Platform / Security / Ops
audience: All contributors
phase: Documentation Bootstrap (M000)
related:
  - ../11-Deployment/README.md
  - ../16-Operations/README.md
---

# Phase 09 — Production (GA)  ⭐ Production-Ready

> **Status: COMPLETE (buildable scope, M009); GA sign-off pending operational acceptance.**
> Delivered: the umbrella Helm chart + four profile overlays, hardened Dockerfiles, the
> supply-chain release pipeline + Kyverno admission (ADR-0015), Envoy Gateway edge (ADR-0014),
> air-gap bundle tooling + a CI no-egress assertion, observability + backup/DR, and a CI `deploy`
> job. Live multi-profile deploy, external pen test, and the DR drill are **operational** — see
> [closure/M009-Production-Closure.md](./closure/M009-Production-Closure.md) and
> [../11-Deployment/GAReadiness.md](../11-Deployment/GAReadiness.md).

> **Purpose.** Harden the platform to production quality across **all** deployment profiles,
> including a validated **air-gapped** path — this is GA.

## Objective
Achieve production readiness: reliability, security, performance, observability, backup/DR,
and validated deployment across cloud/on-prem/hybrid/air-gapped.

## Scope
- All deployment profiles validated ([../11-Deployment/README.md](../11-Deployment/README.md)),
  incl. offline bundle ([../11-Deployment/AirGappedDeployment.md](../11-Deployment/AirGappedDeployment.md)).
- Full observability + SLOs + alerting + runbooks ([../16-Operations/README.md](../16-Operations/README.md)).
- Backup/DR tested ([../16-Operations/BackupRecovery.md](../16-Operations/BackupRecovery.md)).
- Security hardening + external pen test; supply-chain (SBOM/signing/provenance) complete.
- Performance/load validation + capacity/sizing guides.

## Dependencies
- Core feature phases (03–08) at required maturity.

## Deliverables
- A signed, reproducible release deployable to every profile; runbooks; sizing guides;
  passing pen test; DR drill evidence.

## Implementation Requirements
- Zero-downtime upgrades; forward-only migrations; admission-time image verification.

## Tests
- Full security suite + pen test; performance/load; DR restore drills; air-gapped
  no-egress assertion ([../15-Testing/README.md](../15-Testing/README.md)).

## Security Requirements
- All threat-model mitigations covered by tests; critical/high findings remediated
  ([../10-Security/SecurityTesting.md](../10-Security/SecurityTesting.md)).

## Documentation
- Deployment/ops/runbook/sizing docs complete; release notes; update PROJECT_STATE.

## Acceptance Criteria
- Identical release deploys and passes acceptance on all four profiles; DR drill meets
  RPO/RTO; pen test has no unresolved critical/high.

## Definition of Done
- Global DoD + above; **platform is production-ready (GA)**.
