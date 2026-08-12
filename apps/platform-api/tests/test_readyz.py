"""Readiness reflects DB reachability (regression: status label must track the check)."""

from __future__ import annotations

from typing import cast

from fastapi import FastAPI
from fastapi.testclient import TestClient


class _FakeConn:
    async def execute(self, *_: object) -> None:
        return None


class _FakeCtx:
    async def __aenter__(self) -> _FakeConn:
        return _FakeConn()

    async def __aexit__(self, *_: object) -> bool:
        return False


class _OkEngine:
    def connect(self) -> _FakeCtx:
        return _FakeCtx()


class _DownEngine:
    def connect(self) -> _FakeCtx:
        raise RuntimeError("db down")


def test_readyz_ok_when_db_reachable(client: TestClient) -> None:
    cast(FastAPI, client.app).state.engine = _OkEngine()
    resp = client.get("/readyz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "checks": {"database": "ok"}}


def test_readyz_degraded_when_db_down(client: TestClient) -> None:
    cast(FastAPI, client.app).state.engine = _DownEngine()
    resp = client.get("/readyz")
    assert resp.status_code == 503
    assert resp.json() == {"status": "degraded", "checks": {"database": "unavailable"}}
