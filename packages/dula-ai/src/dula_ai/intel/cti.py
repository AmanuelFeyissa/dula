"""CTI extraction service (UC-05 — docs/03-Architecture/RAGArchitecture.md).

Combines the deterministic intel core (IOC + ATT&CK extraction → STIX bundle) with an optional
**grounded, non-speculative summary** produced through the LLM Gateway. The structured
extraction is authoritative and always available offline; the narrative summary is best-effort
and passes the same output guardrails (secret redaction, no injection follow-through) as every
other AI call. The advisory is untrusted data throughout (T2 — indirect prompt injection).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dula_ai import guardrails
from dula_ai.gateway import LLMGateway
from dula_ai.intel.attack import Technique, extract_techniques
from dula_ai.intel.iocs import Indicator, extract
from dula_ai.intel.stix import build_bundle
from dula_ai.prompts import CTI_PROMPT_VERSION, build_cti_summary_prompt

_SUMMARY_MAX_TOKENS = 400


@dataclass(frozen=True, slots=True)
class CTIResult:
    indicators: list[Indicator]
    techniques: list[Technique]
    stix_bundle: dict[str, Any]
    summary: str | None = None
    input_flags: list[str] = field(default_factory=list)


def _structured_facts(indicators: list[Indicator], techniques: list[Technique]) -> str:
    ioc_lines = [f"- {ind.kind}: {ind.defanged}" for ind in indicators] or ["- (none)"]
    ttp_lines = [f"- {t.id} {t.name} ({t.tactic})" for t in techniques] or ["- (none)"]
    return "INDICATORS:\n" + "\n".join(ioc_lines) + "\n\nTECHNIQUES:\n" + "\n".join(ttp_lines)


class CTIService:
    """Extract structured intel from an advisory, optionally with a grounded summary."""

    def __init__(self, gateway: LLMGateway | None = None) -> None:
        self._gateway = gateway

    async def extract(
        self, *, advisory: str, tenant: str, subject: str, summarize: bool = True
    ) -> CTIResult:
        guard = guardrails.check_input(advisory, max_chars=40_000)
        if not guard.allowed:
            raise ValueError(guard.reason or "advisory rejected")

        indicators = extract(advisory)
        techniques = extract_techniques(advisory)
        bundle = build_bundle(indicators, techniques)

        summary: str | None = None
        if summarize and self._gateway is not None:
            system, user = build_cti_summary_prompt(
                advisory, _structured_facts(indicators, techniques)
            )
            result = await self._gateway.generate(
                tenant=tenant,
                subject=subject,
                task="cti-summary",
                system=system,
                user=user,
                max_tokens=_SUMMARY_MAX_TOKENS,
                input_flags=guard.flags,
            )
            out = guardrails.check_output(result.text, [], require_citation=False)
            summary = result.text if out.allowed else "[redacted: output withheld by guardrail]"

        return CTIResult(
            indicators=indicators,
            techniques=techniques,
            stix_bundle=bundle,
            summary=summary,
            input_flags=guard.flags,
        )


CTI_SUMMARY_VERSION = CTI_PROMPT_VERSION
