# ADR-0011: Repository Model — Monorepo

- Status: Accepted
- Date: 2026-08-12
- Deciders: Project owner (user), Architecture
- Related: [../00-Governance/RepositoryGovernance.md](../00-Governance/RepositoryGovernance.md), [../01-Project/ProjectStructure.md](../01-Project/ProjectStructure.md)

## Context
Phase 01 requires a repository model. Dula Platform (Product 1) and Dula AI (Product 2)
share versioned contracts, an evaluation harness, and deployment tooling, but must remain
independently deployable. The bootstrap recommendation (RepositoryGovernance.md) was a
monorepo, left open as an ADR-0011 candidate.

## Options Considered
1. **Monorepo** — one repository for both products, shared libraries, and infra; per-service
   build/release pipelines preserve independent deployability.
2. **Polyrepo** (`dula-platform` + `dula-ai`) — cleaner product separation, but duplicates
   CI, contracts, and the shared eval harness and complicates cross-product changes.

## Decision
**Monorepo.** A single private repository named **`dula`** holds both products, shared
packages, ML assets, deployment tooling, and documentation, following the layout in
[../01-Project/ProjectStructure.md](../01-Project/ProjectStructure.md). Independent
deployability is preserved via per-service container images and release pipelines.

## Consequences
- Atomic cross-product changes (contracts, eval harness); one CI system and one source of
  truth. Requires path-scoped CI and CODEOWNERS to keep builds/reviews targeted.
- Repository governance (branches, PRs, releases) in RepositoryGovernance.md applies
  repo-wide.

## Compliance / Verification
- Per-service pipelines build/release only affected components; CODEOWNERS routes reviews by
  path.
