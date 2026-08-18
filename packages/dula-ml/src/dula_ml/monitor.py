"""Scheduled production health check + auto-rollback trigger
(docs/09-MLOps/ModelLifecycle.md #3 "Production Monitoring", ../08-AI/EvaluationStrategy.md #5
"Continuous Evaluation").

Compares a freshly computed evaluation of whatever is currently `production` against the
baseline it was promoted with (its own recorded `candidate_eval`), using the same gate
`decide()` uses for a brand-new candidate (docs/09-MLOps/EvaluationPipelines.md) -- no new
scoring logic, just a different baseline to compare against. A regression calls
`dula_ml.lifecycle.rollback`, which appends a registry transition (propose and record,
CLAUDE.md #7): it does not touch a live deployment, and if there is no earlier version to
fall back to, the regression is still reported so an operator can act on it manually.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dula_ml.evaluation import EvalReport, GateResult, decide
from dula_ml.lifecycle import current_production, previous_production, rollback


@dataclass(frozen=True, slots=True)
class MonitorResult:
    checked_version: str
    gate: GateResult
    regressed: bool
    rolled_back_to: str | None


def check_production_health(
    manifest_path: str | Path,
    live_report: EvalReport,
    *,
    quality_tolerance: float = 0.0,
    safety_tolerance: float = 0.0,
    actor: str | None = None,
    note: str = "",
) -> MonitorResult:
    """Raises ValueError if nothing is currently in production."""
    production = current_production(manifest_path)
    if production is None:
        raise ValueError("no version is currently in production; nothing to monitor")

    gate = decide(
        live_report,
        production.candidate_eval,
        min_quality_delta=-quality_tolerance,
        safety_tolerance=safety_tolerance,
    )
    regressed = not gate.ship
    rolled_back_to: str | None = None
    if regressed:
        target = previous_production(manifest_path)
        if target is not None:
            rolled = rollback(
                manifest_path,
                actor=actor,
                note=note or f"production drift detected: {'; '.join(gate.reasons)}",
                target=target,
            )
            rolled_back_to = rolled.version

    return MonitorResult(
        checked_version=production.version,
        gate=gate,
        regressed=regressed,
        rolled_back_to=rolled_back_to,
    )
