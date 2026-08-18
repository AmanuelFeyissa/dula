"""Regression test: the audit hook must surface Usage.routed_provider (M011 PR B/C),
not just the outer provider's static `model` name -- otherwise a canary rollout is
unobservable in the domain event a monitoring/alerting pipeline would consume."""

from __future__ import annotations

from dula_ai.gateway import AuditRecord
from dula_ai.types import Usage
from dula_ai_gateway.main import _make_audit_hook
from dula_common.events import EventEnvelope


class _FakePublisher:
    def __init__(self) -> None:
        self.published: list[EventEnvelope] = []

    async def publish(self, envelope: EventEnvelope) -> bool:
        self.published.append(envelope)
        return True


async def test_audit_hook_surfaces_routed_provider_in_the_event() -> None:
    publisher = _FakePublisher()
    audit = _make_audit_hook(publisher)
    record = AuditRecord(
        tenant="tenant-1",
        subject="user-1",
        task="ask",
        model="canary[extractive-v1->openai-compat-dula-ai-v2]",
        usage=Usage(
            prompt_tokens=10, completion_tokens=5, routed_provider="openai-compat-dula-ai-v2"
        ),
        cached=False,
    )

    await audit(record)

    assert len(publisher.published) == 1
    envelope = publisher.published[0]
    assert envelope.data["routed_provider"] == "openai-compat-dula-ai-v2"


async def test_audit_hook_reports_none_when_no_canary_is_wired() -> None:
    publisher = _FakePublisher()
    audit = _make_audit_hook(publisher)
    record = AuditRecord(
        tenant="tenant-1",
        subject="user-1",
        task="ask",
        model="extractive-v1",
        usage=Usage(prompt_tokens=10, completion_tokens=5),
        cached=False,
    )

    await audit(record)

    envelope = publisher.published[0]
    assert envelope.data["routed_provider"] is None
