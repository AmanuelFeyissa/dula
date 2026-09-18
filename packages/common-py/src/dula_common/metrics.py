"""Prometheus metrics for the Dula services (docs/16-Operations/Observability.md).

The names here are the contract `deploy/observability/prometheus-rules.yaml` and the Grafana
dashboard already query:

- ``http_requests_total{service, method, route, code}`` and
  ``http_request_duration_seconds{service, method, route}`` -- recorded by
  ``PrometheusMiddleware`` (pure ASGI, so this package needs no web-framework dependency).
  ``route`` is the matched *template* (``/api/v1/assets/{asset_id}``), never the raw path, so
  ids don't explode the label set.
- ``ai_call_total{service, provider}`` / ``ai_call_errors_total{service, provider}`` and
  ``ai_call_duration_seconds`` -- ``provider`` is the canary *role* (``production`` /
  ``candidate``), which is what the ``DulaCanaryRegression`` rule compares. The AI Gateway
  records these around each LLM provider call (``dula_ai.metering``).

Labels never carry tenant ids, subjects, or prompt content.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable, Iterable, MutableMapping
from typing import Any

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

HTTP_REQUESTS = Counter(
    "http_requests_total",
    "HTTP requests handled.",
    ["service", "method", "route", "code"],
)
HTTP_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency.",
    ["service", "method", "route"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 0.8, 1.0, 2.5, 5.0, 10.0),
)
AI_CALLS = Counter("ai_call_total", "LLM provider calls.", ["service", "provider"])
AI_CALL_ERRORS = Counter(
    "ai_call_errors_total", "LLM provider calls that raised.", ["service", "provider"]
)
AI_CALL_DURATION = Histogram(
    "ai_call_duration_seconds",
    "LLM provider call latency.",
    ["service", "provider"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)


def render_metrics() -> tuple[bytes, str]:
    """The exposition body and its content type, for a ``GET /metrics`` handler."""
    return generate_latest(), CONTENT_TYPE_LATEST


Scope = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[MutableMapping[str, Any]]]
Send = Callable[[MutableMapping[str, Any]], Awaitable[None]]
ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]


class MetricsEndpoint:
    """A raw ASGI ``/metrics`` endpoint: ``app.mount("/metrics", MetricsEndpoint())``."""

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        body, content_type = render_metrics()
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"content-type", content_type.encode("latin-1")),
                    (b"content-length", str(len(body)).encode("latin-1")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})


def route_template(routes: Iterable[Any], scope: Scope) -> str:
    """The path template of the route that matches ``scope``, or ``unmatched``."""
    for route in routes:
        matches = getattr(route, "matches", None)
        if matches is None:
            continue
        match, _ = matches(scope)
        if getattr(match, "name", "") == "FULL":
            return str(getattr(route, "path", "unmatched"))
    return "unmatched"


class PrometheusMiddleware:
    """Records request count + latency per matched route template and status code.

    ``routes`` is the app's live route table (``app.router.routes``); it is read per request,
    so routers included after the middleware is added are still resolved.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        service: str,
        routes: Iterable[Any],
        skip_paths: tuple[str, ...] = ("/metrics",),
    ) -> None:
        self._app = app
        self._service = service
        self._routes = routes
        self._skip = skip_paths

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http" or scope.get("path") in self._skip:
            await self._app(scope, receive, send)
            return

        status = {"code": 500}
        started = time.perf_counter()

        async def send_wrapper(message: MutableMapping[str, Any]) -> None:
            if message.get("type") == "http.response.start":
                status["code"] = int(message.get("status", 500))
            await send(message)

        try:
            await self._app(scope, receive, send_wrapper)
        finally:
            elapsed = time.perf_counter() - started
            method = str(scope.get("method", "GET"))
            route = route_template(self._routes, scope)
            HTTP_REQUESTS.labels(self._service, method, route, str(status["code"])).inc()
            HTTP_DURATION.labels(self._service, method, route).observe(elapsed)
