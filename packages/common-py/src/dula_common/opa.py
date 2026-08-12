"""Open Policy Agent decision client (ADR-0009, docs/12-API/Authorization.md).

Authorization is externalized to OPA/Rego and enforced at the service layer. This client
queries a single decision (default ``dula/authz/allow``) over OPA's Data API. It **fails
closed**: any error (OPA unreachable, malformed response) yields *deny*, so an outage can
never widen access.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

_log = logging.getLogger(__name__)


class OPAClient:
    """Async client for a boolean OPA decision."""

    def __init__(
        self,
        base_url: str,
        *,
        decision_path: str = "dula/authz/allow",
        timeout: float = 2.0,
    ) -> None:
        self._url = f"{base_url.rstrip('/')}/v1/data/{decision_path.strip('/')}"
        self._timeout = timeout

    async def allow(self, input_doc: dict[str, Any]) -> bool:
        """Return the ``allow`` decision for ``input_doc``; deny on any failure."""
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                resp = await client.post(self._url, json={"input": input_doc})
                resp.raise_for_status()
                data: dict[str, Any] = resp.json()
        except (httpx.HTTPError, ValueError) as exc:
            _log.warning("OPA decision unavailable; failing closed", extra={"error": str(exc)})
            return False
        return data.get("result") is True
