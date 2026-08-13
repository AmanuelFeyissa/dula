"""Benchmark gates for CTI extraction and detection authoring (Phase 05 acceptance criteria).

Asserts the deterministic intel capabilities clear a baseline: extraction precision/recall and
100% syntactic validity of authored detections. Runs offline in CI so intel quality cannot
regress silently.
"""

from __future__ import annotations

from dula_ai.intel.benchmark import (
    CTI_BENCHMARK,
    DETECTION_BENCHMARK,
    score_cti,
)
from dula_ai.intel.detections import sigma, yara
from dula_ai.intel.iocs import extract

# Baselines: extraction must be highly precise and recall the labelled indicators/TTPs.
IOC_PRECISION_BASELINE = 0.85
IOC_RECALL_BASELINE = 0.9
TTP_RECALL_BASELINE = 0.9


def test_cti_extraction_meets_baseline() -> None:
    score = score_cti()
    assert score.ioc.precision >= IOC_PRECISION_BASELINE, score
    assert score.ioc.recall >= IOC_RECALL_BASELINE, score
    assert score.technique.recall >= TTP_RECALL_BASELINE, score


def test_authored_detections_are_all_syntactically_valid() -> None:
    for case in DETECTION_BENCHMARK:
        indicators = extract(case.advisory)
        _, sig_text, sig_result = sigma.build_ioc_rule(
            title=case.title,
            indicators=indicators,
            logsource=sigma.LogSource(category="proxy"),
            attack_tags=case.attack_tags,
        )
        assert sig_result.valid, (case.title, sig_result.errors)
        assert sigma.validate_text(sig_text).valid

        name = "Rule_" + str(abs(hash(case.title)) % 100000)
        _, yar_text, yar_result = yara.build_ioc_rule(name=name, indicators=indicators)
        assert yar_result.valid, (case.title, yar_result.errors)
        assert yara.validate_text(yar_text).valid


def test_benchmark_is_non_trivial() -> None:
    # Guard against an empty/degenerate benchmark silently passing.
    assert len(CTI_BENCHMARK) >= 3
    assert len(DETECTION_BENCHMARK) >= 2
