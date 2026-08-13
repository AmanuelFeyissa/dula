"""Offline high-volume ingestion benchmark (Phase 08 scale-test, ADR-0004).

Validates the *processing* path (the CPU-bound work the worker does per event) at volume without a
broker: correctness and idempotency must hold across a high-volume mixed stream, and per-event
processing cost must stay well under a conservative floor so a single consumer keeps up with a
realistic telemetry rate. **True cluster-scale load testing** (a real Redpanda cluster + a load
generator measuring end-to-end lag under partitioned parallelism) is documented as the operational
load test in docs/16-Operations — this test guards the per-event work that such a test would drive.
"""

from __future__ import annotations

import time
import uuid

from dula_common.events import EventEnvelope
from dula_worker.processor import EventProcessor, InMemoryIdempotencyStore

_VOLUME = 20_000
_DUP_RATE = 5  # every 5th event is a redelivery of the previous one (at-least-once)


def _stream(volume: int) -> list[EventEnvelope]:
    events: list[EventEnvelope] = []
    tenant = str(uuid.uuid4())
    previous: EventEnvelope | None = None
    for i in range(volume):
        if previous is not None and i % _DUP_RATE == 0:
            events.append(previous)  # redelivery of the same id
        else:
            previous = EventEnvelope(type="log.ingested", tenant_id=tenant, data={"seq": i})
            events.append(previous)
    return events


async def test_high_volume_ingest_is_correct_and_fast() -> None:
    processor = EventProcessor(InMemoryIdempotencyStore())
    events = _stream(_VOLUME)
    unique_ids = {e.id for e in events}

    start = time.perf_counter()
    handled = 0
    for event in events:
        if await processor.handle(event):
            handled += 1
    elapsed = time.perf_counter() - start

    # Correctness at volume: each unique event handled exactly once; duplicates all skipped.
    assert handled == len(unique_ids)
    assert handled < _VOLUME  # duplicates were present and were deduped

    # Throughput floor: comfortably clears a realistic single-consumer telemetry rate. The bound is
    # deliberately loose (CI runners vary) but still catches a large per-event regression.
    per_event_us = (elapsed / _VOLUME) * 1_000_000
    assert per_event_us < 200, f"per-event processing too slow: {per_event_us:.1f}µs"


async def test_dedupe_holds_across_the_whole_stream() -> None:
    processor = EventProcessor(InMemoryIdempotencyStore())
    events = _stream(2_000)
    first_pass = 0
    for event in events:
        if await processor.handle(event):
            first_pass += 1
    # A full redelivery of the entire stream must be fully skipped (idempotent).
    second_pass = 0
    for event in events:
        if await processor.handle(event):
            second_pass += 1
    assert first_pass == len({e.id for e in events})
    assert second_pass == 0
