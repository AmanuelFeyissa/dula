"""Health endpoint tests."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from dula_ai_gateway.config import Settings
from dula_ai_gateway.main import create_app
from fastapi.testclient import TestClient


def _client() -> Iterator[TestClient]:
    app = create_app(Settings(profile="offline", events_enabled=False, seed_demo_corpus=False))
    with TestClient(app) as client:
        yield client


def test_healthz() -> None:
    for client in _client():
        resp = client.get("/healthz")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


def test_readyz() -> None:
    for client in _client():
        assert client.get("/readyz").status_code == 200


def test_ask_requires_auth() -> None:
    for client in _client():
        # No bearer token, no dependency override → 401.
        resp: Any = client.post("/api/v1/ask", json={"question": "hello"})
        assert resp.status_code == 401
