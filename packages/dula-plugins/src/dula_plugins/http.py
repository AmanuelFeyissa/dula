"""The one HTTP path a connector has to the outside (ConnectorStandards.md §5, PluginSecurity.md).

Every request is checked by the plugin's ``EgressGuard`` first (allowlist + SSRF + air-gap), so
a connector cannot reach a host its manifest did not declare. Redirects are never followed --
a redirect target is an undeclared host until it has been checked, so a 3xx is a failure, not a
hop. Response bodies are capped and returned as **untrusted** data. Nothing here logs headers,
because the ``Authorization`` value is the connector's secret.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx

from dula_plugins.egress import EgressError, EgressGuard


class HttpError(Exception):
    """A request that was permitted by the guard but failed (transport, status, size, shape)."""


@dataclass(frozen=True, slots=True)
class HttpResponse:
    status: int
    body: bytes

    def json(self) -> Any:
        try:
            return json.loads(self.body.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise HttpError(f"response is not JSON: {exc}") from exc


class EgressHttpClient:
    """``httpx`` behind the egress guard: checked URL, no redirects, bounded body, fixed timeout."""

    def __init__(
        self,
        guard: EgressGuard,
        *,
        timeout_seconds: float = 10.0,
        max_response_bytes: int = 1_000_000,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._guard = guard
        self._timeout = timeout_seconds
        self._max_bytes = max_response_bytes
        self._transport = transport

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
        json_body: Any | None = None,
    ) -> HttpResponse:
        self._guard.check(url)  # raises EgressError; callers map it to a connector failure
        async with httpx.AsyncClient(
            timeout=self._timeout, follow_redirects=False, transport=self._transport
        ) as client:
            try:
                async with client.stream(
                    method, url, headers=headers, params=params, json=json_body
                ) as resp:
                    if 300 <= resp.status_code < 400:
                        raise HttpError(f"redirect ({resp.status_code}) refused")
                    chunks: list[bytes] = []
                    size = 0
                    async for chunk in resp.aiter_bytes():
                        size += len(chunk)
                        if size > self._max_bytes:
                            raise HttpError(f"response exceeds {self._max_bytes} bytes")
                        chunks.append(chunk)
                    return HttpResponse(status=resp.status_code, body=b"".join(chunks))
            except httpx.HTTPError as exc:
                raise HttpError(f"{type(exc).__name__}: {exc}") from exc

    async def get_json(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, str] | None = None,
    ) -> Any:
        resp = await self.request("GET", url, headers=headers, params=params)
        if resp.status >= 400:
            raise HttpError(f"HTTP {resp.status}")
        return resp.json()

    async def post_json(self, url: str, body: Any, *, headers: dict[str, str] | None = None) -> Any:
        resp = await self.request("POST", url, headers=headers, json_body=body)
        if resp.status >= 400:
            raise HttpError(f"HTTP {resp.status}")
        return resp.json()


def auth_headers(secret: str | None) -> dict[str, str]:
    """An ``Authorization`` header from a scoped secret (the full header value), or nothing."""
    return {"Authorization": secret} if secret else {}


__all__ = ["EgressError", "EgressHttpClient", "HttpError", "HttpResponse", "auth_headers"]
