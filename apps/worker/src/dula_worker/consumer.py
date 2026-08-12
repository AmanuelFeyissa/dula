"""Kafka/Redpanda consumer loop (transport layer).

Wraps aiokafka with manual offset commits so an event is only acknowledged after it is
processed (at-least-once). The processing itself lives in ``processor.py``.
"""

from __future__ import annotations

import logging

from aiokafka import AIOKafkaConsumer
from dula_common.events import decode_envelope

from dula_worker.config import Settings
from dula_worker.processor import EventProcessor

_log = logging.getLogger(__name__)


async def run(settings: Settings, processor: EventProcessor | None = None) -> None:
    processor = processor or EventProcessor()
    consumer = AIOKafkaConsumer(
        settings.events_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id=settings.consumer_group,
        enable_auto_commit=False,
        auto_offset_reset="earliest",
    )
    await consumer.start()
    _log.info(
        "worker consuming",
        extra={"topic": settings.events_topic, "group": settings.consumer_group},
    )
    try:
        async for msg in consumer:
            try:
                envelope = decode_envelope(msg.value)
                await processor.handle(envelope)
            except Exception as exc:
                _log.warning("failed to process message", extra={"error": str(exc)})
            await consumer.commit()
    finally:
        await consumer.stop()
