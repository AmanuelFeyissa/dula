"""SFT record model + formatting (docs/08-AI/FineTuningStrategy.md, DatasetStrategy.md).

A normalized instruction-tuning record with provenance, plus mappers from common upstream
shapes (e.g. Primus-Instruct) and a chat-template renderer. Kept torch-free so formatting is
identical in CI and on the GPU runner.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class SFTRecord(BaseModel):
    """One supervised fine-tuning example with provenance."""

    instruction: str = Field(min_length=1)
    output: str = Field(min_length=1)
    input: str = ""
    source: str = "unknown"
    license: str = "unknown"
    meta: dict[str, Any] = Field(default_factory=dict)

    def to_messages(self, system: str | None = None) -> list[dict[str, str]]:
        user = self.instruction if not self.input else f"{self.instruction}\n\n{self.input}"
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})
        messages.append({"role": "assistant", "content": self.output})
        return messages

    def to_text(self, system: str | None = None) -> str:
        """Render a simple, explicit chat template (used for datasets libraries without one)."""
        parts: list[str] = []
        if system:
            parts.append(f"<|system|>\n{system}")
        user = self.instruction if not self.input else f"{self.instruction}\n\n{self.input}"
        parts.append(f"<|user|>\n{user}")
        parts.append(f"<|assistant|>\n{self.output}")
        return "\n".join(parts)


def _first(raw: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = raw.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None


def from_raw(raw: dict[str, Any], *, source: str, license: str = "unknown") -> SFTRecord | None:
    """Map a common upstream row (instruction/input/output, question/answer, or messages).

    Returns None for rows that don't carry a usable instruction+output pair.
    """
    # messages-style (OpenAI chat) rows.
    messages = raw.get("messages")
    if isinstance(messages, list):
        user = next((m.get("content") for m in messages if m.get("role") == "user"), None)
        assistant = next((m.get("content") for m in messages if m.get("role") == "assistant"), None)
        if isinstance(user, str) and isinstance(assistant, str) and user and assistant:
            return SFTRecord(instruction=user, output=assistant, source=source, license=license)
        return None

    instruction = _first(raw, "instruction", "question", "prompt", "query")
    output = _first(raw, "output", "answer", "response", "completion")
    if instruction is None or output is None:
        return None
    return SFTRecord(
        instruction=instruction,
        output=output,
        input=_first(raw, "input", "context") or "",
        source=source,
        license=license,
    )
