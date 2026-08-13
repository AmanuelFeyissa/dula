"""Tests for Sigma/YARA authoring, validation, and ATT&CK coverage."""

from __future__ import annotations

from dula_ai.intel.detections import coverage as cov
from dula_ai.intel.detections import sigma, yara
from dula_ai.intel.iocs import extract


def test_sigma_build_ioc_rule_is_valid() -> None:
    inds = extract("c2 evil.com and 8.8.8.8")
    _, text, result = sigma.build_ioc_rule(
        title="Evil C2 beacon",
        indicators=inds,
        logsource=sigma.LogSource(category="proxy"),
        attack_tags=["attack.t1071"],
    )
    assert result.valid, result.errors
    assert "title:" in text and "condition: selection" in text
    # Rendered rule passes the dependency-free text validator too.
    assert sigma.validate_text(text).valid


def test_sigma_condition_referencing_unknown_selection_fails() -> None:
    rule = sigma.SigmaRule(
        title="bad",
        logsource=sigma.LogSource(product="windows"),
        detection={"selection": {"a": "b"}, "condition": "selection and missing"},
    )
    result = sigma.validate(rule)
    assert not result.valid
    assert any("undefined selection" in e for e in result.errors)


def test_sigma_validate_text_missing_keys() -> None:
    result = sigma.validate_text("title: x\n")
    assert not result.valid
    assert any("logsource" in e for e in result.errors)


def test_yara_build_ioc_rule_is_valid() -> None:
    inds = extract("malware talks to evil.com hash " + "a" * 64)
    rule, text, result = yara.build_ioc_rule(name="Evil_Malware", indicators=inds)
    assert result.valid, result.errors
    assert "rule Evil_Malware" in text and "condition:" in text
    # SHA-256 recorded as provenance meta, not as a scan string.
    assert "sha256" in rule.meta
    assert yara.validate_text(text).valid


def test_yara_invalid_name_and_unbalanced_braces() -> None:
    bad = yara.YaraRule(name="1bad", strings=[], condition="true")
    assert not yara.validate(bad).valid
    assert not yara.validate_text("rule X { condition: true").valid  # missing closing brace


def test_yara_condition_undefined_string_fails() -> None:
    rule = yara.YaraRule(name="R", strings=[yara.YaraString("$a", "x")], condition="$a and $b")
    result = yara.validate(rule)
    assert not result.valid
    assert any("$b" in e for e in result.errors)


def test_coverage_reports_gaps_and_ratio() -> None:
    report = cov.coverage(
        [["attack.t1071"], ["attack.t1486"]],
        target=["T1071", "T1486", "T1566"],
    )
    covered_ids = {t.id for t in report.covered_techniques}
    assert {"T1071", "T1486"} <= covered_ids
    assert report.gaps == ["T1566"]
    assert report.coverage_ratio == round(2 / 3, 3)


def test_coverage_parent_covers_subtechnique_target() -> None:
    report = cov.coverage([["attack.t1059"]], target=["T1059.001"])
    assert report.gaps == []
    assert report.coverage_ratio == 1.0
