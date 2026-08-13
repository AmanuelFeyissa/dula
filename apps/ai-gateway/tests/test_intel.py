"""End-to-end tests for the cyber-intelligence endpoints (offline)."""

from __future__ import annotations

from typing import Any

from dula_ai_gateway.deps import RequestContext
from fastapi.testclient import TestClient

Env = tuple[TestClient, dict[str, RequestContext], Any]

_ADVISORY = (
    "APT group sent spearphishing emails. The loader beacons to hxxps://evil[.]example[.]com/gate "
    "and 203.0.113.7, dropping a payload with SHA-256 " + "a" * 64 + ". Tracked as CVE-2024-9999. "
    "Execution via PowerShell (T1059.001)."
)


def test_extract_returns_iocs_ttps_and_stix(env: Env) -> None:
    client, _, _ = env
    resp = client.post("/api/v1/intel/extract", json={"advisory": _ADVISORY, "summarize": False})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    kinds = {i["kind"] for i in body["indicators"]}
    assert {"url", "ipv4", "sha256", "cve"} <= kinds
    # Indicators are defanged in the response (not live links).
    assert all(
        "[.]" in i["defanged"] or i["kind"] in ("cve", "sha256", "sha1", "md5", "ipv6")
        for i in body["indicators"]
    )
    assert {t["id"] for t in body["techniques"]} >= {"T1566", "T1059.001"}
    assert body["stix_bundle"]["type"] == "bundle"


def test_extract_with_summary_uses_gateway(env: Env) -> None:
    client, _, _ = env
    resp = client.post("/api/v1/intel/extract", json={"advisory": _ADVISORY, "summarize": True})
    assert resp.status_code == 200
    assert resp.json()["summary"]


def test_extract_authz_denied(env: Env) -> None:
    client, _, opa = env
    opa.allow_result = False
    resp = client.post("/api/v1/intel/extract", json={"advisory": _ADVISORY, "summarize": False})
    assert resp.status_code == 403


def test_vulnerability_prioritization(env: Env) -> None:
    client, _, _ = env
    resp = client.post(
        "/api/v1/intel/vulnerability",
        json={
            "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H",
            "cve_id": "CVE-2021-44228",
            "known_exploited": True,
            "internet_facing": True,
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["base_score"] == 10.0
    assert body["severity"] == "critical"
    assert body["priority"] == "P1"
    assert body["rationale"]


def test_vulnerability_bad_vector_is_400(env: Env) -> None:
    client, _, _ = env
    resp = client.post("/api/v1/intel/vulnerability", json={"cvss_vector": "AV:N/AC:L"})
    assert resp.status_code == 400


def test_author_sigma_rule_is_valid(env: Env) -> None:
    client, _, _ = env
    resp = client.post(
        "/api/v1/intel/detections/sigma",
        json={
            "title": "Evil C2 beacon",
            "advisory": _ADVISORY,
            "category": "proxy",
            "attack_tags": ["attack.t1071"],
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["valid"] is True
    assert "title:" in body["rule"] and "condition:" in body["rule"]


def test_author_yara_rule_is_valid(env: Env) -> None:
    client, _, _ = env
    resp = client.post(
        "/api/v1/intel/detections/yara",
        json={"name": "Evil_Malware", "advisory": _ADVISORY},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["valid"] is True
    assert "rule Evil_Malware" in body["rule"]


def test_validate_external_sigma_rule(env: Env) -> None:
    client, _, _ = env
    resp = client.post(
        "/api/v1/intel/detections/validate",
        json={"format": "sigma", "rule": "title: x\n"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["valid"] is False
    assert body["errors"]


def test_coverage_report(env: Env) -> None:
    client, _, _ = env
    resp = client.post(
        "/api/v1/intel/detections/coverage",
        json={
            "rule_tag_sets": [["attack.t1071"], ["attack.t1486"]],
            "target": ["T1071", "T1486", "T1566"],
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["gaps"] == ["T1566"]
    assert 0 < body["coverage_ratio"] < 1
