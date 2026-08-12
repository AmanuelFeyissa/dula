"""Test fixtures for the AI Gateway: offline app with swappable caller context + stub OPA."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from dula_ai_gateway.config import Settings
from dula_ai_gateway.deps import RequestContext, get_request_context
from dula_ai_gateway.main import create_app
from fastapi.testclient import TestClient


class StubOPA:
    def __init__(self, allow: bool = True) -> None:
        self.allow_result = allow

    async def allow(self, _input: dict[str, Any]) -> bool:
        return self.allow_result


@pytest.fixture
def env() -> Iterator[tuple[TestClient, dict[str, RequestContext], StubOPA]]:
    settings = Settings(profile="offline", events_enabled=False, seed_demo_corpus=True)
    app = create_app(settings)
    holder = {"ctx": RequestContext(subject="analyst-1", tenant="tenant-x", roles=("analyst",))}
    app.dependency_overrides[get_request_context] = lambda: holder["ctx"]
    with TestClient(app) as client:
        opa = StubOPA(allow=True)
        client.app.state.opa = opa  # type: ignore[attr-defined]
        yield client, holder, opa
