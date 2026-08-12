"""Unit tests for LLM providers (offline extractive + OpenAI-compatible, mocked)."""

from __future__ import annotations

from typing import Any

import pytest
from dula_ai.providers import ExtractiveProvider, OpenAICompatProvider


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
