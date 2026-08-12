---
title: User & Operator Documentation — Overview
document_id: USR-000
status: Draft
version: 0.1.0
last_updated: 2026-08-12
owner: Product / Docs
audience: End User, Administrator, Operator
phase: Phase 01 — Foundation (M001)
related:
  - ../../CLAUDE.md
  - ../00-Governance/DocumentationStandards.md
  - ../04-MVP-Roadmap/closure/README.md
---

# 17 — User & Operator Documentation

> **Purpose.** Home for **user/operator-facing** documentation — how to install, configure,
> use, operate, and troubleshoot Dula — as distinct from the technical/engineering docs in
> areas `00`–`16`. Governed by the closure lifecycle in **CLAUDE.md §11**.

## Audience

End users, administrators, and operators (platform users). These documents explain **how to
use and run** capabilities and **do not** expose unnecessary internal implementation detail.
For *how it works / how it is built*, see the technical areas (`00`–`16`) and `../adr/`.

## Guide Set (created incrementally, per milestone)

Guides are created **only when the corresponding capability is actually usable** (CLAUDE.md
§11.5 — do not document non-existent functionality). Until then a guide is listed here as
**FUTURE**. Maturity tags follow
[../00-Governance/DocumentationStandards.md](../00-Governance/DocumentationStandards.md).

| Guide | Status | Notes |
|-------|--------|-------|
| [Core Entities User Guide](./CoreEntitiesUserGuide.md) | MVP | Alerts, incidents, assets — browse in the web app; create/update via API (Phase 02) |
| [Ask Dula User Guide](./AskDulaUserGuide.md) | MVP | Grounded, cited Q&A and alert triage (Phase 03) |
| Product Overview | FUTURE | User-facing summary; authoritative product scope stays in [../02-Vision/Vision.md](../02-Vision/Vision.md) |
| Installation Guide | FUTURE | Arrives with a packaged/deployable release (Phase 09) |
| Getting Started | MVP | Interim: local dev quickstart in the root [README](../../README.md); user-facing version when UI features land |
| Configuration Guide | FUTURE | When operator-configurable settings exist |
| User Guide | FUTURE | When end-user features exist (Phase 03+) |
| Administrator Guide | FUTURE | Tenant/user/role administration |
| Operator Guide | FUTURE | Running/operating a deployment |
| Feature-Usage Guides | FUTURE | Per feature (triage, hunting, detections, …) |
| API-Usage Guide | FUTURE | Consuming the public API; technical spec in [../12-API/](../12-API/README.md) |
| Troubleshooting Guide | FUTURE | User-facing symptoms/resolutions |
| FAQ | FUTURE | Where useful |
| Security Considerations | FUTURE | User-facing security guidance; authoritative model in [../10-Security/](../10-Security/README.md) |
| Deployment Guide (user) | FUTURE | Operator deployment; technical detail in [../11-Deployment/](../11-Deployment/README.md) |
| Upgrade / Migration Guide | FUTURE | When upgrades exist |
| Backup / Restore Guide | FUTURE | When operator backup/restore exists |

## Conventions

- **Naming/IDs:** `USR` prefix, `PascalCase.md` (e.g. `AuthenticationUserGuide.md`) per
  [../00-Governance/NamingConventions.md](../00-Governance/NamingConventions.md).
- **Cross-reference** each user guide with its technical counterpart and vice versa
  (CLAUDE.md §11.10) — e.g. user `AuthenticationUserGuide.md` ↔ technical
  [../12-API/Authentication.md](../12-API/Authentication.md).
- **No duplication:** link to the authoritative technical/vision doc rather than restating it.

## Current State

Phase 02 delivered browsing of alerts, incidents, and assets in the web app (create/update via
the API) — see the [Core Entities User Guide](./CoreEntitiesUserGuide.md). Phase 03 adds the
first AI capability: grounded, cited Q&A and alert triage — see the
[Ask Dula User Guide](./AskDulaUserGuide.md). The interim getting-started path remains the
local-dev quickstart in the root [README](../../README.md). Further user guides are added as
features become usable, closed out per **CLAUDE.md §11**.
