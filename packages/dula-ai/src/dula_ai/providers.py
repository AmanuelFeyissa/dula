"""LLM providers behind the gateway (ADR-0005).

Providers are interchangeable. `ExtractiveProvider` is the **offline default**: it composes a
grounded answer purely by extracting text from the delimited EVIDENCE blocks in the prompt —
it never follows instructions embedded in that (untrusted) content, which makes it a useful,
deterministic reference for tests and a genuinely air-gapped answerer. `OllamaProvider` calls a
local Ollama server (dev serving); vLLM/llama.cpp adapters follow the same protocol.
"""

from __future__ import annotations

import re
from typing import Protocol

from dula_ai.text import estimate_tokens
from dula_ai.types import Usage

_EVIDENCE_RE = re.compile(r"<<<EVIDENCE (\d+)>>>\n(.*?)\n<<<END \1>>>", re.DOTALL)
_WS_RE = re.compile(r"\s+")


class LLMProvider(Protocol):
    name: str

    async def generate(self, system: str, user: str, *, max_tokens: int) -> tuple[str, Usage]: ...


def _snippet(text: str, limit: int = 240) -> str:
    collapsed = _WS_RE.sub(" ", text).strip()
    return collapsed if len(collapsed) <= limit else collapsed[:limit].rsplit(" ", 1)[0] + "…"


class ExtractiveProvider:
    """Deterministic, offline grounded answerer built from EVIDENCE blocks."""

    name = "extractive-v1"

    async def generate(self, system: str, user: str, *, max_tokens: int) -> tuple[str, Usage]:
        blocks = _EVIDENCE_RE.findall(user)
        if not blocks:
            answer = "I do not have enough information in the provided evidence to answer."
        else:
            parts = [f"{_snippet(text)} [{marker}]" for marker, text in blocks[:2]]
            answer = "Based on the retrieved evidence: " + " ".join(parts)
        usage = Usage(
            prompt_tokens=estimate_tokens(system) + estimate_tokens(user),
            completion_tokens=estimate_tokens(answer),
        )
        return answer, usage


class OllamaProvider:
    """Local Ollama chat provider (ADR-0005 dev serving). Optional; requires a running server."""

    def __init__(self, model: str, base_url: str = "http://localhost:11434") -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")
        self.name = f"ollama-{model}"

    async def generate(self, system: str, user: str, *, max_tokens: int) -> tuple[str, Usage]:
        import httpx

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "stream": False,
                    "options": {"num_predict": max_tokens},
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
            )
            resp.raise_for_status()
            data = resp.json()
        text = data["message"]["content"]
        usage = Usage(
            prompt_tokens=int(data.get("prompt_eval_count", estimate_tokens(system + user))),
            completion_tokens=int(data.get("eval_count", estimate_tokens(text))),
        )
        return text, usage


class OpenAICompatProvider:
    """OpenAI-compatible chat provider — serves the tuned Dula AI model via vLLM / llama.cpp.

    Points at any ``/v1``-style endpoint (vLLM, llama.cpp server, or a hosted endpoint). This is
    how a shipped Dula AI checkpoint (Phase 04) is served behind the gateway without app changes.
    """

    def __init__(self, model: str, base_url: str, api_key: str | None = None) -> None:
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self.name = f"openai-compat-{model}"

    async def generate(self, system: str, user: str, *, max_tokens: int) -> tuple[str, Usage]:
        import httpx

        headers = {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self._base_url}/chat/completions",
                headers=headers,
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.0,
                },
            )
            resp.raise_for_status()
            data = resp.json()
        text = data["choices"][0]["message"]["content"]
        usage_raw = data.get("usage") or {}
        usage = Usage(
            prompt_tokens=int(usage_raw.get("prompt_tokens", estimate_tokens(system + user))),
            completion_tokens=int(usage_raw.get("completion_tokens", estimate_tokens(text))),
        )
        return text, usage
