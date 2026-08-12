"""Guardrails (docs/03-Architecture/AIArchitecture.md §4, AIThreatModel.md).

Input guardrails: size limits and prompt-injection heuristics (T1). Output guardrails:
citation enforcement for grounded tasks (T12 — misinformation) and a secret-leakage check
(T5/T13). The primary injection defense is structural — untrusted content is delimited and
labelled in `prompts.py`, and the model is told to treat it as data — these heuristics are
defense-in-depth and observability, not the sole control.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from dula_ai.types import Citation

_INJECTION_PATTERNS = [
    re.compile(r"ignore (all |the |your )?(previous|prior|above) (instructions|prompts?)", re.I),
    re.compile(r"disregard (the |your |all )?(previous|prior|above|system)", re.I),
    re.compile(r"you are now\b", re.I),
    re.compile(r"reveal (your |the )?(system )?(prompt|instructions)", re.I),
    re.compile(r"\bdeveloper mode\b", re.I),
    re.compile(r"\bjailbreak\b", re.I),
    re.compile(r"print (your |the )?(system )?(prompt|instructions)", re.I),
]

_SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),  # AWS access key id
    re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b"),  # Slack token
]


@dataclass(frozen=True, slots=True)
class GuardrailResult:
    allowed: bool
    reason: str | None = None
    flags: list[str] = field(default_factory=list)


def detect_injection(text: str) -> list[str]:
    return [p.pattern for p in _INJECTION_PATTERNS if p.search(text)]


def check_input(
    text: str, *, max_chars: int = 8000, block_on_injection: bool = False
) -> GuardrailResult:
    """Validate a user query before it enters the pipeline."""
    if not text.strip():
        return GuardrailResult(allowed=False, reason="empty query")
    if len(text) > max_chars:
        return GuardrailResult(allowed=False, reason="query too large")
    flags = detect_injection(text)
    if flags and block_on_injection:
        return GuardrailResult(allowed=False, reason="possible prompt injection", flags=flags)
    return GuardrailResult(allowed=True, flags=flags)


def contains_secret(text: str) -> bool:
    return any(p.search(text) for p in _SECRET_PATTERNS)


def referenced_citations(answer_text: str, citations: list[Citation]) -> list[Citation]:
    """Return only the citations the answer actually references via [n] markers."""
    markers = {int(m) for m in re.findall(r"\[(\d+)\]", answer_text)}
    return [c for c in citations if c.marker in markers]


def check_output(
    answer_text: str, citations: list[Citation], *, require_citation: bool
) -> GuardrailResult:
    """Validate a model answer for a grounded task."""
    if contains_secret(answer_text):
        return GuardrailResult(allowed=False, reason="output contained a secret-like pattern")
    if require_citation and citations and not referenced_citations(answer_text, citations):
        return GuardrailResult(allowed=False, reason="grounded answer missing citations")
    return GuardrailResult(allowed=True)
