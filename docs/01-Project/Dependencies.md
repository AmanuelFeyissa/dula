---
title: Dependencies & Licensing Policy
document_id: PRJ-004
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Engineering Governance
audience: Engineers, security, legal liaison
phase: Documentation Bootstrap (M000)
related:
  - ./TechnologyStack.md
  - ../10-Security/SupplyChainSecurity.md
---

# Dependencies & Licensing Policy

> **Purpose.** Define how third-party dependencies (libraries, container base images,
> models, and datasets) are selected, licensed, pinned, scanned, and maintained.

## 1. Principles

- **Minimize.** Prefer the standard library and existing dependencies over adding new
  ones. Every dependency is attack surface and maintenance burden.
- **Permissive by default.** Because the product ships to customers (including air-gapped
  enterprises), prefer permissive licenses.
- **Pin & lock.** All dependencies are pinned with committed lockfiles.
- **Scan continuously.** Vulnerabilities and license violations block merges/releases.

## 2. License Policy

| Category | Examples | Policy |
|----------|----------|--------|
| Permissive | MIT, BSD, Apache-2.0, ISC | **Allowed** |
| Weak copyleft | MPL-2.0, LGPL | **Allowed with review** (dynamic linking / isolation) |
| Strong copyleft | GPL, AGPL | **Restricted** — requires explicit approval; AGPL avoided for anything network-served in the product |
| Non-commercial / research-only | CC-BY-NC, some model licenses | **Not allowed** in shipped product; may be used for internal research only, clearly quarantined |
| Unknown / missing | — | **Blocked** until resolved |

- This applies equally to **model weights** and **datasets**. Model and dataset licenses
  are frequently *not* OSS licenses and often restrict commercial or derivative use —
  each is reviewed individually (see [../08-AI/ModelSelection.md](../08-AI/ModelSelection.md)
  and [../08-AI/DatasetStrategy.md](../08-AI/DatasetStrategy.md)). **REQUIRES RESEARCH**
  per model/dataset.

## 3. Dependency Management by Ecosystem

- **Python:** `pyproject.toml` + `uv` lockfile; no unpinned ranges in production.
- **TypeScript:** `package.json` + committed lockfile (`pnpm-lock.yaml`).
- **Containers:** pinned base images by digest; minimal/distroless where possible.
- **Models/Datasets:** versioned and hash-addressed (see
  [../09-MLOps/DatasetVersioning.md](../09-MLOps/DatasetVersioning.md)).

## 4. Supply-Chain Controls

- Generate an **SBOM** per artifact; sign images and produce provenance attestations.
- Automated scans in CI: dependency CVEs, license compliance, secret scanning.
- Pull-through/mirror registry for air-gapped installs (no direct internet at deploy time).
- See [../10-Security/SupplyChainSecurity.md](../10-Security/SupplyChainSecurity.md).

## 5. Adding a Dependency (Checklist)

1. Is it necessary, or can existing tools do it?
2. License compatible (§2)?
3. Actively maintained, reasonable transitive footprint?
4. Security history acceptable; passes CVE scan?
5. Works air-gapped (no phone-home / mandatory external calls)?
6. Pinned + lockfile updated; SBOM regenerates cleanly?

## 6. Maintenance

- Scheduled dependency-update cadence with automated PRs and full test/scan gates.
- Security patches expedited per [../16-Operations/IncidentManagement.md](../16-Operations/IncidentManagement.md).
