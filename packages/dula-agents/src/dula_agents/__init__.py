"""Dula agent runtime (Phase 06 — docs/03-Architecture/AgentArchitecture.md, ADR-0008).

A safe plan/act loop: a planner proposes tool calls, and a first-party runtime enforces the
**security-critical layer** — per-call permission checks (agent ⊆ user), human approval for
consequential actions, step/loop/cost limits, and a full replayable audit trace. **The model
never executes anything and never self-grants tools**; the runtime is the only component that
runs a tool, and only after the checks pass.

Per ADR-0008 the execution graph may later be backed by LangGraph; the runtime interface here
abstracts that so the security controls stay first-party and testable regardless of the engine.
Everything runs **offline** by default (deterministic planner + in-memory tools/broker/audit),
so agent behaviour is reproducible in CI and works air-gapped.
"""

from __future__ import annotations
