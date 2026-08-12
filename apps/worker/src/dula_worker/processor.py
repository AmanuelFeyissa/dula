"""Idempotent event processing (pure, transport-agnostic — unit-testable).

Delivery on the bus is at-least-once, so the same event may arrive more than once. The
processor dedupes by ``event.id`` via a pluggable idempotency store and dispatches by event
type. Keeping this free of Kafka lets it be tested without a broker.
"""

from __future__ import annotations

import logging
from typing import Protocol
from uuid import UUID

from dula_common.events import EventEnvelope

_log = logging.getLogger(__name__)


class IdempotencyStore(Protocol):
    """Records which event ids have already been processed."""

    def seen(self, event_id: UUID) -> bool: ...

    def mark(self, event_id: UUID) -> None: ...


class InMemoryIdempotencyStore:
    """Process-local dedupe. A durable (Redis/Postgres) store replaces this at scale."""

    def __init__(self) -> None:
        self._seen: set[UUID] = set()

    def seen(self, event_id: UUID) -> bool:
        return event_id in self._seen

    def mark(self, event_id: UUID) -> None:
        self._seen.add(event_id)


class EventProcessor:
    def __init__(self, store: IdempotencyStore | None = None) -> None:
        self._store = store or InMemoryIdempotencyStore()

    async def handle(self, envelope: EventEnvelope) -> bool:
        """Process one event. Returns True if handled, False if a duplicate was skipped."""
        if self._store.seen(envelope.id):
            _log.info("duplicate event skipped", extra={"event_id": str(envelope.id)})
            return False
        self._dispatch(envelope)
        self._store.mark(envelope.id)
        return True

    def _dispatch(self, envelope: EventEnvelope) -> None:
        # Phase 02 baseline: structured acknowledgement. Enrichment (asset correlation,
        # indexing to OpenSearch/Qdrant) is layered on in later phases.
        _log.info(
            "processed domain event",
            extra={
                "event_id": str(envelope.id),
                "type": envelope.type,
                "tenant_id": envelope.tenant_id,
            },
        )
