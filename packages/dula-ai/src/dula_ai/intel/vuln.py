"""Vulnerability analysis (UC-07 — docs/02-Vision/UseCases.md).

Deterministic CVSS v3.1 base-score computation from a vector string plus a transparent
prioritization model that combines the technical severity with contextual signals
(known-exploited, internet exposure, asset criticality, patch availability). The scoring is a
pure function implementing the official CVSS v3.1 specification, so results are auditable and
reproducible offline — no model, no network. A model may add narrative context on top (via the
gateway), but the *priority decision* is explainable arithmetic, never a black box.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from enum import StrEnum

# CVSS v3.1 metric weights (spec §7.4).
_AV = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.20}
_AC = {"L": 0.77, "H": 0.44}
_UI = {"N": 0.85, "R": 0.62}
_CIA = {"N": 0.0, "L": 0.22, "H": 0.56}
_PR_UNCHANGED = {"N": 0.85, "L": 0.62, "H": 0.27}
_PR_CHANGED = {"N": 0.85, "L": 0.68, "H": 0.50}

_VECTOR_RE = re.compile(r"\b([A-Z]+):([A-Z])\b")


class Severity(StrEnum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Priority(StrEnum):
    P1 = "P1"  # remediate immediately
    P2 = "P2"  # remediate this cycle
    P3 = "P3"  # schedule
    P4 = "P4"  # monitor / accept


class CvssError(ValueError):
    """Raised when a CVSS vector is malformed or missing required base metrics."""


def _roundup(value: float) -> float:
    """CVSS v3.1 Roundup: round up to one decimal (spec Appendix A)."""
    int_input = round(value * 100_000)
    if int_input % 10_000 == 0:
        return int_input / 100_000.0
    return (math.floor(int_input / 10_000) + 1) / 10.0


def severity_of(score: float) -> Severity:
    """Qualitative severity rating for a CVSS base score (spec §5)."""
    if score <= 0.0:
        return Severity.NONE
    if score < 4.0:
        return Severity.LOW
    if score < 7.0:
        return Severity.MEDIUM
    if score < 9.0:
        return Severity.HIGH
    return Severity.CRITICAL


@dataclass(frozen=True, slots=True)
class CvssResult:
    base_score: float
    severity: Severity
    metrics: dict[str, str]


def parse_cvss_vector(vector: str) -> CvssResult:
    """Compute the CVSS v3.1 base score from a vector string.

    Accepts an optional ``CVSS:3.1/`` prefix. Raises :class:`CvssError` if any of the eight
    mandatory base metrics (AV, AC, PR, UI, S, C, I, A) is missing or invalid.
    """
    metrics = {k: v for k, v in _VECTOR_RE.findall(vector.upper()) if k != "CVSS"}
    required = ("AV", "AC", "PR", "UI", "S", "C", "I", "A")
    missing = [m for m in required if m not in metrics]
    if missing:
        raise CvssError(f"missing base metrics: {', '.join(missing)}")

    scope_changed = metrics["S"] == "C"
    try:
        av, ac, ui = _AV[metrics["AV"]], _AC[metrics["AC"]], _UI[metrics["UI"]]
        pr = (_PR_CHANGED if scope_changed else _PR_UNCHANGED)[metrics["PR"]]
        conf, integ, avail = _CIA[metrics["C"]], _CIA[metrics["I"]], _CIA[metrics["A"]]
    except KeyError as exc:
        raise CvssError(f"invalid metric value: {exc}") from exc

    iss = 1 - (1 - conf) * (1 - integ) * (1 - avail)
    impact = 7.52 * (iss - 0.029) - 3.25 * (iss - 0.02) ** 15 if scope_changed else 6.42 * iss
    exploitability = 8.22 * av * ac * pr * ui

    if impact <= 0:
        base = 0.0
    elif scope_changed:
        base = _roundup(min(1.08 * (impact + exploitability), 10))
    else:
        base = _roundup(min(impact + exploitability, 10))
    return CvssResult(base_score=base, severity=severity_of(base), metrics=metrics)


@dataclass(frozen=True, slots=True)
class Signals:
    """Contextual risk signals layered on top of the technical CVSS score."""

    known_exploited: bool = False  # e.g. present in CISA KEV / observed in the wild
    internet_facing: bool = False
    asset_criticality: str = "medium"  # low | medium | high
    patch_available: bool = True


@dataclass(frozen=True, slots=True)
class Prioritization:
    priority: Priority
    risk_score: float  # 0-100, transparent weighted blend
    severity: Severity
    base_score: float
    rationale: list[str] = field(default_factory=list)


_CRITICALITY = {"low": -10.0, "medium": 0.0, "high": 10.0}


def prioritize(base_score: float, signals: Signals) -> Prioritization:
    """Blend CVSS severity with exploitation/exposure context into an explainable priority.

    The risk score is a 0-100 weighted sum: CVSS contributes up to 70, active exploitation and
    internet exposure are the dominant multipliers, and asset criticality nudges the result.
    Every contributing factor is recorded in ``rationale`` so the decision is reviewable.
    """
    reasons: list[str] = []
    risk = base_score * 7.0  # 0-70
    reasons.append(f"CVSS base {base_score} ({severity_of(base_score).value})")

    if signals.known_exploited:
        risk += 20.0
        reasons.append("known-exploited in the wild (KEV) — major escalation")
    if signals.internet_facing:
        risk += 12.0
        reasons.append("asset is internet-facing")
    if not signals.patch_available:
        risk += 4.0
        reasons.append("no patch available yet — compensating controls required")
    crit_adj = _CRITICALITY.get(signals.asset_criticality, 0.0)
    if crit_adj:
        risk += crit_adj
        reasons.append(f"asset criticality: {signals.asset_criticality}")

    risk = max(0.0, min(100.0, risk))
    if (signals.known_exploited and base_score >= 7.0) or risk >= 80:
        priority = Priority.P1
    elif risk >= 60:
        priority = Priority.P2
    elif risk >= 35:
        priority = Priority.P3
    else:
        priority = Priority.P4
    return Prioritization(
        priority=priority,
        risk_score=round(risk, 1),
        severity=severity_of(base_score),
        base_score=base_score,
        rationale=reasons,
    )
