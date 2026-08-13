"""Tests for ATT&CK extraction and STIX 2.1 mapping."""

from __future__ import annotations

from dula_ai.intel.attack import extract_techniques, lookup
from dula_ai.intel.iocs import extract
from dula_ai.intel.stix import build_bundle


def test_extract_explicit_technique_id() -> None:
    techs = extract_techniques("The actor used T1059.001 for execution.")
    assert any(t.id == "T1059.001" for t in techs)


def test_extract_technique_by_keyword() -> None:
    techs = extract_techniques("The campaign began with a spearphishing email attachment.")
    assert any(t.id == "T1566" for t in techs)


def test_lookup_falls_back_to_parent() -> None:
    tech = lookup("T1003.001")
    assert tech is not None and tech.id == "T1003"


def test_extract_ransomware_impact() -> None:
    techs = extract_techniques("Files were encrypted and a ransom note was dropped.")
    assert any(t.id == "T1486" for t in techs)


def test_stix_bundle_is_deterministic_and_well_formed() -> None:
    text = "c2 at evil.com dropping T1486 ransomware, hash " + "a" * 64
    inds = extract(text)
    techs = extract_techniques(text)
    bundle = build_bundle(inds, techs)
    assert bundle["type"] == "bundle"
    types = {o["type"] for o in bundle["objects"]}
    assert "indicator" in types and "attack-pattern" in types
    # Deterministic: same input → identical bundle (idempotent).
    assert build_bundle(inds, techs) == bundle
    for obj in bundle["objects"]:
        if obj["type"] == "indicator":
            assert obj["pattern"].startswith("[") and obj["pattern_type"] == "stix"


def test_stix_indicator_pattern_paths() -> None:
    inds = extract("domain evil.com ip 8.8.8.8")
    bundle = build_bundle(inds, [])
    patterns = [o["pattern"] for o in bundle["objects"]]
    assert any("domain-name:value = 'evil.com'" in p for p in patterns)
    assert any("ipv4-addr:value = '8.8.8.8'" in p for p in patterns)
