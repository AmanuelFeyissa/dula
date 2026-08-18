"""Unit tests for LLM providers (offline extractive + OpenAI-compatible, mocked)."""

from __future__ import annotations

from typing import Any

import pytest
from dula_ai.providers import CanaryProvider, ExtractiveProvider, OpenAICompatProvider
from dula_ai.types import Usage


async def test_extractive_provider_cites_evidence() -> None:
    user = "EVIDENCE:\n[1] (source: s)\n<<<EVIDENCE 1>>>\nMFA blocks brute force.\n<<<END 1>>>"
    text, usage = await ExtractiveProvider().generate("sys", user, max_tokens=64)
    assert "[1]" in text
    assert usage.total_tokens > 0


async def test_extractive_provider_no_evidence() -> None:
    text, _ = await ExtractiveProvider().generate("sys", "QUESTION only", max_tokens=64)
    assert "enough information" in text.lower()


class _FakeResp:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return {
            "choices": [{"message": {"content": "MFA blocks it [1]"}}],
            "usage": {"prompt_tokens": 7, "completion_tokens": 3},
        }


class _FakeClient:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        pass

    async def __aenter__(self) -> _FakeClient:
        return self

    async def __aexit__(self, *args: Any) -> bool:
        return False

    async def post(self, *args: Any, **kwargs: Any) -> _FakeResp:
        return _FakeResp()


async def test_openai_compat_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("httpx.AsyncClient", _FakeClient)
    provider = OpenAICompatProvider("dula-ai", "http://gateway/v1", api_key="k")
    text, usage = await provider.generate("system", "user", max_tokens=16)
    assert text == "MFA blocks it [1]"
    assert usage.prompt_tokens == 7 and usage.completion_tokens == 3
    assert provider.name == "openai-compat-dula-ai"


class _StubProvider:
    def __init__(self, name: str, reply: str = "reply") -> None:
        self.name = name
        self.reply = reply
        self.calls = 0

    async def generate(self, system: str, user: str, *, max_tokens: int) -> tuple[str, Usage]:
        self.calls += 1
        return self.reply, Usage(prompt_tokens=1, completion_tokens=1)


async def test_canary_provider_rejects_out_of_range_weight() -> None:
    prod, cand = _StubProvider("prod"), _StubProvider("cand")
    with pytest.raises(ValueError, match="candidate_weight"):
        CanaryProvider(prod, cand, candidate_weight=1.5)


async def test_canary_provider_zero_weight_always_routes_to_production() -> None:
    prod, cand = _StubProvider("prod"), _StubProvider("cand")
    canary = CanaryProvider(prod, cand, candidate_weight=0.0)
    for i in range(20):
        text, usage = await canary.generate("sys", f"question {i}", max_tokens=16)
        assert text == "reply"
        assert usage.routed_provider == "prod"
    assert prod.calls == 20
    assert cand.calls == 0


async def test_canary_provider_full_weight_always_routes_to_candidate() -> None:
    prod, cand = _StubProvider("prod"), _StubProvider("cand")
    canary = CanaryProvider(prod, cand, candidate_weight=1.0)
    for i in range(20):
        _, usage = await canary.generate("sys", f"question {i}", max_tokens=16)
        assert usage.routed_provider == "cand"
    assert prod.calls == 0
    assert cand.calls == 20


async def test_canary_provider_routing_is_deterministic_per_prompt() -> None:
    prod, cand = _StubProvider("prod"), _StubProvider("cand")
    canary = CanaryProvider(prod, cand, candidate_weight=0.5)
    _, first = await canary.generate("sys", "the exact same question", max_tokens=16)
    _, second = await canary.generate("sys", "the exact same question", max_tokens=16)
    assert first.routed_provider == second.routed_provider


async def test_canary_provider_weight_converges_over_many_distinct_prompts() -> None:
    prod, cand = _StubProvider("prod"), _StubProvider("cand")
    canary = CanaryProvider(prod, cand, candidate_weight=0.3)
    n = 2000
    for i in range(n):
        await canary.generate("sys", f"distinct question number {i}", max_tokens=16)
    fraction_to_candidate = cand.calls / n
    assert 0.3 - 0.05 <= fraction_to_candidate <= 0.3 + 0.05


async def test_canary_provider_name_reflects_both_providers() -> None:
    prod, cand = _StubProvider("prod"), _StubProvider("cand")
    canary = CanaryProvider(prod, cand, candidate_weight=0.5)
    assert "prod" in canary.name
    assert "cand" in canary.name
