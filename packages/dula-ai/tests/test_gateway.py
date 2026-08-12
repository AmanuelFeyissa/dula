"""Unit tests for the LLM Gateway: budgets, per-tenant cache isolation, audit, redaction."""

from __future__ import annotations

import pytest
from dula_ai.gateway import AuditRecord, BudgetExceeded, LLMGateway
from dula_ai.providers import ExtractiveProvider
from dula_ai.types import Usage


class _CountingProvider:
    name = "counter"

    def __init__(self) -> None:
        self.calls = 0

    async def generate(self, system: str, user: str, *, max_tokens: int) -> tuple[str, Usage]:
        self.calls += 1
        return f"answer {self.calls}", Usage(prompt_tokens=10, completion_tokens=5)


async def test_response_cache_avoids_second_provider_call() -> None:
    provider = _CountingProvider()
    gw = LLMGateway(provider)
    r1 = await gw.generate(tenant="t1", subject="u", task="qa", system="s", user="u")
    r2 = await gw.generate(tenant="t1", subject="u", task="qa", system="s", user="u")
    assert provider.calls == 1
    assert r1.cached is False and r2.cached is True
    assert r1.text == r2.text


async def test_cache_is_not_shared_across_tenants() -> None:
    provider = _CountingProvider()
    gw = LLMGateway(provider)
    a = await gw.generate(tenant="tenant-a", subject="u", task="qa", system="s", user="u")
    b = await gw.generate(tenant="tenant-b", subject="u", task="qa", system="s", user="u")
    # A distinct provider call happened for tenant B — no cross-tenant cache reuse (ADR-0006).
    assert provider.calls == 2
    assert b.cached is False
    assert a.text != b.text


async def test_budget_enforced_per_tenant() -> None:
    gw = LLMGateway(_CountingProvider(), max_tokens_per_tenant=10)
    await gw.generate(tenant="t1", subject="u", task="qa", system="s", user="u1")  # uses 15 > cap
    with pytest.raises(BudgetExceeded):
        await gw.generate(tenant="t1", subject="u", task="qa", system="s", user="u2")
    # A different tenant still has budget.
    await gw.generate(tenant="t2", subject="u", task="qa", system="s", user="u2")


async def test_audit_hook_receives_record() -> None:
    records: list[AuditRecord] = []

    async def audit(rec: AuditRecord) -> None:
        records.append(rec)

    gw = LLMGateway(ExtractiveProvider(), audit=audit)
    await gw.generate(tenant="t1", subject="maya", task="qa", system="s", user="no evidence here")
    assert len(records) == 1
    assert records[0].tenant == "t1" and records[0].subject == "maya"


async def test_secret_output_is_redacted() -> None:
    class LeakyProvider:
        name = "leaky"

        async def generate(self, system: str, user: str, *, max_tokens: int) -> tuple[str, Usage]:
            return "here: AKIAIOSFODNN7EXAMPLE", Usage(prompt_tokens=1, completion_tokens=1)

    gw = LLMGateway(LeakyProvider())
    result = await gw.generate(tenant="t1", subject="u", task="qa", system="s", user="u")
    assert "AKIA" not in result.text
    assert "redacted" in result.text
