---
title: Core Entities User Guide (Alerts, Incidents, Assets)
document_id: USR-001
status: Draft
version: 0.1.0
last_updated: 2026-08-12
owner: Product / Docs
audience: End User, Operator
phase: Phase 02 — Core Platform (M002)
related:
  - ./README.md
  - ../12-API/CoreDomainAPI.md
  - ../12-API/Authentication.md
---

# Core Entities User Guide

> **Purpose.** How to sign in and work with Dula's core security-operations entities —
> **alerts**, **incidents**, and **assets** — via the web app and the API. **Status: MVP.**
> Technical reference: [../12-API/CoreDomainAPI.md](../12-API/CoreDomainAPI.md).

## What you can do today

Phase 02 delivers the SOC/IR spine. In the **web app** you can sign in with your
organization account and **browse and open** alerts, incidents, and assets for your tenant.
**Creating and editing** entities is available through the **API** (web forms arrive in a
later phase). You only ever see data belonging to your own tenant.

## Signing in

1. Open the web app (default `http://localhost:3000` in local development).
2. Choose **Sign in with Keycloak** and authenticate.
3. Use the top navigation to move between **Alerts**, **Incidents**, and **Assets**.
4. **Sign out** from the top-right when finished.

If you are not signed in, protected pages show a **Sign in required** prompt.

## Browsing and viewing

- Each list shows the most recent items with key fields (e.g. severity, status).
- Select an item's title to open its **detail** view. Alerts link through to any related
  incident or asset.

## Creating and updating (via API)

Your access token authorizes each call; you can only act within your tenant, and your role
determines which actions are allowed (see *Permissions* below). Example — raise an alert:

```bash
TOKEN=...   # your Keycloak access token
curl -sX POST http://localhost:8000/api/v1/alerts \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"title":"suspicious login","severity":"high","source":"edr"}'
```

Full endpoint and field reference: [../12-API/CoreDomainAPI.md](../12-API/CoreDomainAPI.md).

## Permissions (roles)

- **Analyst / Hunter** — read everything; create and triage alerts.
- **Responder** — read everything; manage incidents; update alerts.
- **Engineer** — read everything; manage assets and alerts.
- **Admin** — full access.

An action outside your role returns **not authorized (403)**; data outside your tenant
appears as **not found (404)**.

## Troubleshooting

- **Sign-in prompt won't go away / “API unreachable”** — the Platform API or Keycloak may be
  down; confirm the local stack is running (`make up`).
- **403 not authorized** — your role does not permit that action; ask an administrator.
- **404 not found** — the item does not exist *in your tenant* (it may belong to another).

## Deleting

Deleting an item is a **soft delete** — it disappears from lists and detail views but is
retained internally for audit/history.
