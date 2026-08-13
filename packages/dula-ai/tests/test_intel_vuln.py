"""Tests for CVSS v3.1 scoring and prioritization."""

from __future__ import annotations

import pytest
from dula_ai.intel.vuln import (
    CvssError,
    Priority,
    Severity,
    Signals,
    parse_cvss_vector,
    prioritize,
    severity_of,
)


def test_cvss_known_vectors() -> None:
    # Log4Shell-style fully critical vector.
    r = parse_cvss_vector("CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H")
    assert r.base_score == 10.0
    assert r.severity is Severity.CRITICAL


def test_cvss_medium_vector() -> None:
    r = parse_cvss_vector("AV:N/AC:H/PR:L/UI:R/S:U/C:L/I:L/A:N")
    assert 3.0 <= r.base_score <= 6.9
    assert r.severity in (Severity.LOW, Severity.MEDIUM)


def test_cvss_none_when_no_impact() -> None:
    r = parse_cvss_vector("AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N")
    assert r.base_score == 0.0
    assert r.severity is Severity.NONE


def test_cvss_missing_metric_raises() -> None:
    with pytest.raises(CvssError):
        parse_cvss_vector("AV:N/AC:L/PR:N/UI:N/S:U/C:H")


def test_severity_thresholds() -> None:
    assert severity_of(0.0) is Severity.NONE
    assert severity_of(3.9) is Severity.LOW
    assert severity_of(4.0) is Severity.MEDIUM
    assert severity_of(7.0) is Severity.HIGH
    assert severity_of(9.0) is Severity.CRITICAL


def test_prioritize_kev_high_is_p1() -> None:
    p = prioritize(8.8, Signals(known_exploited=True, internet_facing=True))
    assert p.priority is Priority.P1
    assert any("KEV" in r for r in p.rationale)


def test_prioritize_low_context_is_low_priority() -> None:
    p = prioritize(4.0, Signals(asset_criticality="low"))
    assert p.priority in (Priority.P3, Priority.P4)
    assert p.risk_score < 60


def test_prioritize_rationale_is_transparent() -> None:
    p = prioritize(9.0, Signals(internet_facing=True, patch_available=False))
    assert p.base_score == 9.0
    assert any("internet-facing" in r for r in p.rationale)
    assert any("no patch" in r for r in p.rationale)
