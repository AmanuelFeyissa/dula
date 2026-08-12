"""LLM Gateway (docs/03-Architecture/AIArchitecture.md §2).

The single choke point for AI consumption: model routing, per-tenant token/cost budgets
(T15 — unbounded consumption), a **per-tenant** response cache (never shared across tenants —
ADR-0006 / T14), output secret-leakage guard, token accounting, and an audit hook. Callers
never bind to a specific model/runtime.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from dula_ai.guardrails import contains_secret
from dula_ai.providers import LLMProvider
from dula_ai.types import Usage


class BudgetExceeded(Exception):
    """Raised when a tenant exceeds its token budget (mapped to HTTP 429 by callers)."""


@dataclass(frozen=True, slots=True)
class GatewayResult:
    text: str
    usage: Usage
    model: str
    cached: bool


@dataclass(frozen=True, slots=True)
class AuditRecord:
    tenant: str
    subject: str
    task: str
    model: str
    usage: Usage
    cached: bool
    input_flags: list[str] = field(default_factory=list)


AuditHook = Callable[[AuditRecord], Awaitable[None]]
Router = Callable[[str], LLMProvider]


class LLMGateway:
    def __init__(
        self,
        provider: LLMProvider,
        *,
        max_tokens_per_tenant: int = 200_000,
        audit: AuditHook | None = None,
        router: Router | None = None,
    ) -> None:
        self._default_provider = provider
        self._router = router
        self._cap = max_tokens_per_tenant
        self._audit = audit
        self._used: dict[str, int] = defaultdict(int)
        # Cache key is (tenant, digest); tenant is part of the key, so no entry is ever shared
        # across tenants.
        self._cache: dict[tuple[str, str], GatewayResult] = {}

    def tokens_used(self, tenant: str) -> int:
        return self._used[tenant]

    def _provider_for(self, task: str) -> LLMProvider:
        return self._router(task) if self._router else self._default_provider

    async def generate(
        self,
        *,
        tenant: str,
        subject: str,
        task: str,
        system: str,
        user: str,
        max_tokens: int = 512,
        input_flags: list[str] | None = None,
    ) -> GatewayResult:
        provider = self._provider_for(task)
        digest = hashlib.sha256(f"{provider.name}|{system}|{user}".encode()).hexdigest()
        key = (tenant, digest)

        cached = self._cache.get(key)
        if cached is not None:
            result = GatewayResult(cached.text, cached.usage, cached.model, cached=True)
            await self._emit_audit(tenant, subject, task, result, input_flags)
            return result

        if self._used[tenant] >= self._cap:
            raise BudgetExceeded(f"tenant {tenant} exceeded token budget ({self._cap})")

        text, usage = await provider.generate(system, user, max_tokens=max_tokens)
        if contains_secret(text):
            text = "[redacted: output withheld by guardrail]"

        self._used[tenant] += usage.total_tokens
        result = GatewayResult(text=text, usage=usage, model=provider.name, cached=False)
        self._cache[key] = result
        await self._emit_audit(tenant, subject, task, result, input_flags)
        return result

    async def _emit_audit(
        self,
        tenant: str,
        subject: str,
        task: str,
        result: GatewayResult,
        input_flags: list[str] | None,
    ) -> None:
        if self._audit is None:
            return
        await self._audit(
            AuditRecord(
                tenant=tenant,
                subject=subject,
                task=task,
                model=result.model,
                usage=result.usage,
                cached=result.cached,
                input_flags=input_flags or [],
            )
        )
