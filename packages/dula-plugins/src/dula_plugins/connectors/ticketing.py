"""Ticketing connector (`ticketing.create_ticket`, consequential).

A **consequential** outbound action: it creates a ticket in an external system. Direct callers
must hold the capability's permission, and when driven by an agent the create is additionally
**human-approval-gated** (docs/13-Agents/HumanApproval.md). Two backends: an in-memory sink so
contract tests need no live calls, and a generic REST backend (JSON POST through the egress
guard, ``Idempotency-Key`` header) that fits most ticketing APIs behind a small adapter.
Supports an idempotency key (ConnectorStandards.md §3).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

import httpx

from dula_plugins.connector import ConnectorContext, ConnectorResult
from dula_plugins.egress import EgressError
from dula_plugins.http import EgressHttpClient, HttpError, auth_headers
from dula_plugins.manifest import Capability, PluginManifest, SideEffect
from dula_plugins.sdk import BaseConnector

TICKETING_PLUGIN_ID = "dula-plugin-dula-ticketing"
TICKETING_SECRET_KEY = "ticketing.authorization"  # noqa: S105 - name only; value in the provider


class TicketBackend(Protocol):
    async def create(
        self,
        tenant: str,
        title: str,
        body: str,
        idempotency_key: str | None,
        ctx: ConnectorContext,
    ) -> str: ...


@dataclass
class FixtureTicketBackend:
    created: list[dict[str, str]] = field(default_factory=list)
    _by_key: dict[str, str] = field(default_factory=dict)

    async def create(
        self,
        tenant: str,
        title: str,
        body: str,
        idempotency_key: str | None,
        ctx: ConnectorContext,
    ) -> str:
        if idempotency_key and idempotency_key in self._by_key:
            return self._by_key[idempotency_key]  # idempotent: same key → same ticket
        ticket_id = f"TICKET-{len(self.created) + 1}"
        self.created.append({"id": ticket_id, "tenant": tenant, "title": title, "body": body})
        if idempotency_key:
            self._by_key[idempotency_key] = ticket_id
        return ticket_id


@dataclass
class HttpTicketBackend:
    """POST ``{"title", "body", "tenant"}`` to ``create_url``; the ticket id is ``id_field``.

    The idempotency key travels as an ``Idempotency-Key`` header so a retried create after a
    timeout can't open two tickets on a system that honours it. Auth comes from the scoped
    secret ``ticketing.authorization`` and is never logged.
    """

    create_url: str
    id_field: str = "id"
    transport: httpx.AsyncBaseTransport | None = None

    async def create(
        self,
        tenant: str,
        title: str,
        body: str,
        idempotency_key: str | None,
        ctx: ConnectorContext,
    ) -> str:
        headers = auth_headers(ctx.secrets.get(TICKETING_SECRET_KEY))
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        client = EgressHttpClient(ctx.egress, transport=self.transport or ctx.transport)
        data = await client.post_json(
            self.create_url, {"title": title, "body": body, "tenant": tenant}, headers=headers
        )
        ticket_id = data.get(self.id_field) if isinstance(data, dict) else None
        if ticket_id is None or ticket_id == "":
            raise HttpError(f"response has no '{self.id_field}'")
        return str(ticket_id)


def ticketing_manifest(egress: list[str] | None = None) -> PluginManifest:
    return PluginManifest(
        id=TICKETING_PLUGIN_ID,
        version="0.2.0",
        publisher_key_id="dula-builtin",
        description="First-party ticketing connector (consequential).",
        egress=list(egress or []),
        capabilities=[
            Capability(
                name="ticketing.create_ticket",
                side_effect=SideEffect.CONSEQUENTIAL,
                permission="connector.ticketing.create",
                description="Create an incident ticket in the external system.",
            )
        ],
    )


class TicketingConnector(BaseConnector):
    def __init__(self, backend: TicketBackend, *, egress: list[str] | None = None) -> None:
        super().__init__(ticketing_manifest(egress))
        self._backend = backend
        self.register("ticketing.create_ticket", self._create)

    async def _create(self, args: dict[str, Any], ctx: ConnectorContext) -> ConnectorResult:
        title = args.get("title")
        if not isinstance(title, str) or not title.strip():
            return ConnectorResult(ok=False, error="missing 'title'")
        body = args.get("body", "")
        body = body if isinstance(body, str) else ""
        key = args.get("idempotency_key")
        key = key if isinstance(key, str) else None
        try:
            ticket_id = await self._backend.create(ctx.tenant, title, body, key, ctx)
        except EgressError as exc:
            return ConnectorResult(ok=False, error=f"egress denied: {exc}")
        except HttpError as exc:
            return ConnectorResult(ok=False, error=f"ticketing request failed: {exc}")
        return ConnectorResult(ok=True, output={"ticket_id": ticket_id})
