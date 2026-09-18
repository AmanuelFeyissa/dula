"""MeteredProvider records ai_call_* under the canary role, including on the error path."""

from __future__ import annotations

import pytest
from dula_ai.metering import MeteredProvider
from dula_ai.providers import CanaryProvider, ExtractiveProvider
from dula_ai.types import Usage
from dula_common.metrics import AI_CALL_ERRORS, AI_CALLS


class _Failing:
    name = "openai-compat-broken"

    async def generate(self, system: str, user: str, *, max_tokens: int) -> tuple[str, Usage]:
        raise ConnectionError("upstream down")


def _calls(role: str) -> float:
    return float(AI_CALLS.labels("svc", role)._value.get())


def _errors(role: str) -> float:
    return float(AI_CALL_ERRORS.labels("svc", role)._value.get())


async def test_success_counts_call_but_not_error_and_keeps_name() -> None:
    inner = ExtractiveProvider()
    metered = MeteredProvider(inner, service="svc", role="production")
    assert metered.name == inner.name
    c, e = _calls("production"), _errors("production")
    text, usage = await metered.generate("sys", "what is MFA?", max_tokens=32)
    assert isinstance(text, str) and usage.total_tokens >= 0
    assert _calls("production") == c + 1 and _errors("production") == e


async def test_error_counts_error_and_reraises() -> None:
    metered = MeteredProvider(_Failing(), service="svc", role="candidate")
    c, e = _calls("candidate"), _errors("candidate")
    with pytest.raises(ConnectionError):
        await metered.generate("sys", "u", max_tokens=8)
    assert _calls("candidate") == c + 1 and _errors("candidate") == e + 1


async def test_roles_stay_exact_under_canary_routing() -> None:
    # Each side is metered before composition, so whichever side the canary picks, the
    # counters move under that side's role -- even when the candidate raises.
    production = MeteredProvider(ExtractiveProvider(), service="svc", role="production")
    candidate = MeteredProvider(_Failing(), service="svc", role="candidate")
    canary = CanaryProvider(production, candidate, candidate_weight=1.0)  # always candidate
    e = _errors("candidate")
    with pytest.raises(ConnectionError):
        await canary.generate("sys", "u", max_tokens=8)
    assert _errors("candidate") == e + 1
