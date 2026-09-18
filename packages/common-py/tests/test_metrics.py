"""The /metrics exporter: route-template labels, status codes, and the exposition endpoint."""

from __future__ import annotations

from dula_common.metrics import HTTP_REQUESTS, MetricsEndpoint, PrometheusMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(PrometheusMiddleware, service="test-svc", routes=app.router.routes)
    app.mount("/metrics", MetricsEndpoint(), name="metrics")

    @app.get("/api/v1/things/{thing_id}")
    async def thing(thing_id: str) -> dict[str, str]:
        if thing_id == "missing":
            raise HTTPException(status_code=404)
        return {"id": thing_id}

    return app


def _count(service: str, method: str, route: str, code: str) -> float:
    return float(HTTP_REQUESTS.labels(service, method, route, code)._value.get())


def test_requests_are_counted_by_route_template_not_raw_path() -> None:
    client = TestClient(_app())
    before_ok = _count("test-svc", "GET", "/api/v1/things/{thing_id}", "200")
    before_404 = _count("test-svc", "GET", "/api/v1/things/{thing_id}", "404")

    assert client.get("/api/v1/things/abc-123").status_code == 200
    assert client.get("/api/v1/things/def-456").status_code == 200
    assert client.get("/api/v1/things/missing").status_code == 404

    assert _count("test-svc", "GET", "/api/v1/things/{thing_id}", "200") == before_ok + 2
    assert _count("test-svc", "GET", "/api/v1/things/{thing_id}", "404") == before_404 + 1
    # No per-id series were created.
    assert ("test-svc", "GET", "/api/v1/things/abc-123", "200") not in HTTP_REQUESTS._metrics


def test_unknown_paths_collapse_to_one_series() -> None:
    client = TestClient(_app())
    before = _count("test-svc", "GET", "unmatched", "404")
    client.get("/nope/1")
    client.get("/nope/2")
    assert _count("test-svc", "GET", "unmatched", "404") == before + 2


def test_metrics_endpoint_serves_prometheus_exposition_and_is_not_self_counted() -> None:
    client = TestClient(_app())
    client.get("/api/v1/things/x")
    before = sum(
        float(m._value.get())
        for labels, m in HTTP_REQUESTS._metrics.items()
        if labels[0] == "test-svc" and labels[2] == "/metrics"
    )
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/plain")
    body = resp.text
    assert "http_requests_total" in body and "http_request_duration_seconds_bucket" in body
    assert 'route="/api/v1/things/{thing_id}"' in body
    after = sum(
        float(m._value.get())
        for labels, m in HTTP_REQUESTS._metrics.items()
        if labels[0] == "test-svc" and labels[2] == "/metrics"
    )
    assert after == before  # scraping is not itself a counted request
