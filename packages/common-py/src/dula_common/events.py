"""Event backbone client (ADR-0004, docs/03-Architecture/DataArchitecture.md §2).

Domain events are published to Redpanda (Kafka API) as JSON envelopes. Publishing is
**best-effort and non-blocking to correctness**: if the bus is disabled or unreachable the
producer degrades gracefully (logs and drops), honouring the deploy-anywhere / air-gapped
principle — the request path still succeeds. Delivery is at-least-once; consumers dedupe by
``event.id`` (idempotent consumers).

Event type naming follows ``domain.entity.action`` (NamingConventions.md).
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import uuid
from types import TracebackType
from typing import Any

from aiokafka import AIOKafkaProducer
from pydantic import BaseModel, Field

_log = logging.getLogger(__name__)


class EventEnvelope(BaseModel):
    """A tenant-scoped domain event carried on the bus."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    type: str
    tenant_id: str
    occurred_at: dt.datetime = Field(default_factory=lambda: dt.datetime.now(dt.UTC))
    data: dict[str, Any] = Field(default_factory=dict)

    def to_bytes(self) -> bytes:
        return self.model_dump_json().encode("utf-8")


class EventPublisher:
    """Lazy Kafka/Redpanda producer with graceful degradation."""

    def __init__(
        self,
        bootstrap_servers: str,
        *,
        topic: str = "dula.domain.events",
        enabled: bool = True,
    ) -> None:
        self._bootstrap = bootstrap_servers
        self._topic = topic
        self._enabled = enabled
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        if not self._enabled:
            _log.info("event publishing disabled")
            return
        try:
            producer = AIOKafkaProducer(bootstrap_servers=self._bootstrap)
            await producer.start()
            self._producer = producer
            _log.info("event publisher connected", extra={"bootstrap": self._bootstrap})
        except Exception as exc:
            self._producer = None
            _log.warning("event bus unavailable; events will be dropped", extra={"error": str(exc)})

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None

    async def publish(self, envelope: EventEnvelope) -> bool:
        """Publish an event, keyed by tenant. Returns True if handed to the broker."""
        if self._producer is None:
            _log.debug("event dropped (no producer)", extra={"type": envelope.type})
            return False
        try:
            await self._producer.send_and_wait(
                self._topic,
                value=envelope.to_bytes(),
                key=envelope.tenant_id.encode("utf-8"),
            )
            return True
        except Exception as exc:
            _log.warning("event publish failed", extra={"type": envelope.type, "error": str(exc)})
            return False

    async def __aenter__(self) -> EventPublisher:
        await self.start()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.stop()


def decode_envelope(raw: bytes) -> EventEnvelope:
    """Parse a raw Kafka value back into an envelope (consumer side)."""
    return EventEnvelope.model_validate(json.loads(raw))
