---
title: UI/UX Guidelines
document_id: FE-002
status: Draft
version: 0.1.0
last_updated: 2026-08-11
owner: Frontend / Design
audience: Frontend engineers, designers
phase: Documentation Bootstrap (M000)
related:
  - ./FrontendArchitecture.md
  - ../02-Vision/GuidingPrinciples.md
---

# UI/UX Guidelines

> **Purpose.** Principles for a trustworthy security-analyst experience.

## 1. Design Principles

- **Evidence-first:** AI outputs always show citations/sources; users can drill into
  evidence. Distinguish AI-generated content visually.
- **Trust & transparency:** show uncertainty; never present AI guesses as fact
  ([../02-Vision/GuidingPrinciples.md](../02-Vision/GuidingPrinciples.md)).
- **Human-in-command:** consequential actions require explicit, clear confirmation
  ([../13-Agents/HumanApproval.md](../13-Agents/HumanApproval.md)); show predicted impact.
- **Efficiency:** optimize analyst workflows (triage/hunt/IR); keyboard-friendly; minimal
  context switching.

## 2. Consistency

- Component library (shadcn/ui) + Tailwind design tokens; consistent patterns for tables,
  filters, detail views, and streaming responses.

## 3. Accessibility

- WCAG-minded: contrast, keyboard nav, ARIA, reduced-motion; light/dark themes.

## 4. Data Density

- Security work is data-dense; support progressive disclosure, saved views, and clear
  information hierarchy.

## 5. Safety Cues

- Clear labeling of tenant context, data classification where relevant, and irreversible
  actions.

## 6. Performance

- Stream long AI outputs; paginate/virtualize large lists; avoid blocking the UI.
