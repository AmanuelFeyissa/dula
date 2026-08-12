"""Unit tests for idempotent event processing (no broker required)."""

from __future__ import annotations

import uuid

from dula_common.events import EventEnvelope
from dula_worker.processor import EventProcessor, InMemoryIdempotencyStore


def _event() -> EventEnvelope:
    return EventEnvelope(type="alert.created", tenant_id=str(uuid.uuid4()), data={"id": "1"})


async def test_processes_new_event() -> None:
    processor = EventProcessor(InMemoryIdempotencyStore())
    assert await processor.handle(_event()) is True


async def test_dedupes_by_event_id() -> None:
    store = InMemoryIdempotencyStore()
    processor = EventProcessor(store)
    event = _event()

    assert await processor.handle(event) is True
    # Same id delivered again (at-least-once) is skipped.
    assert await processor.handle(event) is False


async def test_distinct_events_both_processed() -> None:
    processor = EventProcessor(InMemoryIdempotencyStore())
    assert await processor.handle(_event()) is True
    assert await processor.handle(_event()) is True
