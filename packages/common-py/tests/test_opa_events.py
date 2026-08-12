"""Unit tests for the OPA client and event envelope (no external services)."""

from __future__ import annotations

import uuid

from dula_common.events import EventEnvelope, EventPublisher, decode_envelope
from dula_common.opa import OPAClient


async def test_opa_fails_closed_when_unreachable() -> None:
    # Nothing is listening on this port; a failed decision must deny, never allow.
    client = OPAClient("http://127.0.0.1:1", timeout=0.2)
    assert await client.allow({"action": "alerts.read"}) is False


def test_event_envelope_roundtrip() -> None:
    env = EventEnvelope(type="alert.created", tenant_id=str(uuid.uuid4()), data={"id": "42"})
    restored = decode_envelope(env.to_bytes())
    assert restored.id == env.id
    assert restored.type == "alert.created"
    assert restored.data["id"] == "42"


async def test_publisher_disabled_drops_events() -> None:
    publisher = EventPublisher("localhost:19092", enabled=False)
    await publisher.start()
    try:
        env = EventEnvelope(type="alert.created", tenant_id="t1")
        assert await publisher.publish(env) is False
    finally:
        await publisher.stop()
