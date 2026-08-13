"""Tests for the CTI extraction service (deterministic core + grounded summary)."""

from __future__ import annotations

import pytest
from dula_ai.factory import build_offline_stack
from dula_ai.intel.cti import CTIService

_ADVISORY = (
    "Threat actor delivered a spearphishing email with a malicious attachment. "
    "The loader beacons to hxxps://evil[.]example[.]com/gate and 203.0.113.7. "
    "Payload SHA-256: " + "a" * 64 + ". Tracked as CVE-2024-9999. "
    "Post-exploitation used PowerShell (T1059.001)."
)


@pytest.mark.asyncio
async def test_cti_extracts_iocs_ttps_and_stix() -> None:
    svc = CTIService(gateway=None)
    result = await svc.extract(advisory=_ADVISORY, tenant="t1", subject="u1", summarize=False)

    kinds = {i.kind for i in result.indicators}
    assert {"url", "ipv4", "sha256", "cve"} <= kinds
    tech_ids = {t.id for t in result.techniques}
    assert {"T1566", "T1059.001"} <= tech_ids
    assert result.stix_bundle["type"] == "bundle"
    assert result.summary is None


@pytest.mark.asyncio
async def test_cti_grounded_summary_via_gateway() -> None:
    stack = build_offline_stack()
    svc = CTIService(gateway=stack.gateway)
    result = await svc.extract(advisory=_ADVISORY, tenant="t1", subject="u1", summarize=True)
    assert result.summary is not None and result.summary.strip()


@pytest.mark.asyncio
async def test_cti_rejects_empty_advisory() -> None:
    svc = CTIService(gateway=None)
    with pytest.raises(ValueError, match="empty"):
        await svc.extract(advisory="   ", tenant="t1", subject="u1")
