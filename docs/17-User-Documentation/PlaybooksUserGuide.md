---
title: Automation Playbooks — User Guide
document_id: USR-006
status: Draft
version: 0.1.0
last_updated: 2026-08-13
owner: Product / Docs
audience: End User, Operator, Security Engineer
phase: Phase 08 — Automation (M008)
related:
  - ./README.md
  - ./AgentsUserGuide.md
  - ../12-API/AutomationAPI.md
  - ../13-Agents/Playbooks.md
---

# Automation Playbooks — User Guide

> **Purpose.** How to run Dula's supervised security playbooks and read their reports — safely.
> **Status: MVP.** Technical reference: [../13-Agents/Playbooks.md](../13-Agents/Playbooks.md).

## What a playbook is

A **playbook** is a saved, multi-step security procedure — for example *triage an alert, enrich its
indicator, corroborate against logs, and open an incident ticket*. Dula runs the read-only steps for
you automatically and **pauses for your approval** before any consequential action (like creating a
ticket). You always stay in command: **no action is ever taken without your authorization**, and
you can only ever do what your role allows.

Because a playbook runs on the same agent engine as the investigation assistant, all the same
safeguards apply — least privilege, human approval, run limits, and a full audit trail.

## Running a playbook (web)

1. Open **Automation** in the top navigation.
2. Pick a playbook (e.g. **Triage, enrich, and open a ticket**) and select **Run playbook**.
3. Watch the **trace** fill in as the read-only steps run.
4. When a consequential step is reached, an **Approval required** box appears. Review the impact
   (e.g. the ticket that would be created) and choose **Approve** or **Reject**.
   - **Approve** → the action runs and the playbook finishes.
   - **Reject** → the playbook halts and **nothing is created**.
5. Select **Generate report** to produce an executive + technical write-up you can share.

## Reading the report

The report is **grounded** — every statement comes from what the run actually did, and each piece of
evidence cites the step it came from. It has two parts:

- **Executive summary** — how many alerts/indicators/logs were reviewed, what consequential action
  was taken (and who approved it), and the outcome.
- **Technical detail** — a per-step table (what was permitted, whether it needed approval, the
  result) and an evidence list.

If you rejected the action, the report clearly says the ticket was **not** created. Evidence pulled
from tools (logs, threat-intel enrichment) is labelled **untrusted** — it is information to weigh,
not instructions to follow.

## Who can do what

| You want to… | You need the role/permission |
|--------------|------------------------------|
| List and run playbooks | any operational role (`analyst`, `hunter`, `responder`, `engineer`, `admin`) |
| Approve an incident-ticket step | permission for that action (e.g. analyst/responder can create tickets) |
| Read a report | any operational role |

An approver can never approve something beyond their **own** permissions, and the playbook keeps
acting as **you** (the person who started it), not the approver.

## Good to know

- **Air-gapped / offline:** playbooks work fully offline with the built-in demo data; features that
  need an external feed stay inert unless egress is explicitly enabled.
- **Nothing runs on a schedule yet:** you start each run yourself. Scheduled/triggered runs are a
  future capability.
- **One built-in playbook today** (*Triage, enrich, and open a ticket*); more will follow.

## Troubleshooting

| Symptom | Likely cause / fix |
|---------|--------------------|
| “Not authorized” when running | Your role lacks `automation.run`; ask an admin. |
| The run **halted** at the ticket step without asking me | You’re not authorized to create tickets, so the step was refused (not paused). |
| Approve button returns a conflict | The run was already resolved; start a new run. |
| Report shows 0 indicators | The top alert had no indicator to enrich — expected, not an error. |
