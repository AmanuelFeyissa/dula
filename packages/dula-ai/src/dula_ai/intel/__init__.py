"""Cyber-intelligence engineering (Phase 05 — docs/04-MVP-Roadmap/Phase05-CyberIntelligence.md).

Deterministic, offline-first building blocks for CTI extraction (UC-05), vulnerability
analysis (UC-07), and detection authoring (UC-04). The extraction, scoring, and rule
validation here are **pure functions** — no model, no network — so they work air-gapped and
are exactly reproducible in CI. Grounded, cited *summaries* layer the RAG pipeline on top of
this deterministic core (see ``cti.py``).

Security stance (docs/10-Security/AIThreatModel.md): every ingested advisory, CVE record, or
draft rule is **untrusted input**. IOCs are defanged on output so intel never renders as a
live link, and detection authoring is defensive-only.
"""

from __future__ import annotations
