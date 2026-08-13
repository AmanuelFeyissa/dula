"""Ticketing connector (`ticketing.create_ticket`, consequential).

A **consequential** outbound action: it creates a ticket in an external system. Direct callers
must hold the capability's permission, and when driven by an agent the create is additionally
**human-approval-gated** (docs/13-Agents/HumanApproval.md). Offline it records the intent to an
in-memory sink so contract tests need no live calls; a production build would POST via egress.
Supports an idempotency key (ConnectorStandards.md §3).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from dula_plugins.connector import ConnectorContext, ConnectorResult
from dula_plugins.manifest import Capability, PluginManifest, SideEffect
from dula_plugins.sdk import BaseConnector

TICKETING_PLUGIN_ID = "dula-plugin-dula-ticketing"


class TicketBackend(Protocol):
    async def create(
        self, tenant: str, title: str, body: str, idempotency_key: str | None
    ) -> str: ...


@dataclass
class FixtureTicketBackend:
    created: list[dict[str, str]] = field(default_factory=list)
    _by_key: dict[str, str] = field(default_factory=dict)

    async def create(self, tenant: str, title: str, body: str, idempotency_key: str | None) -> str:
        if idempotency_key and idempotency_key in self._by_key:
            return self._by_key[idempotency_key]  # idempotent: same key → same ticket
        ticket_id = f"TICKET-{len(self.created) + 1}"
        self.created.append({"id": ticket_id, "tenant": tenant, "title": title, "body": body})
        if idempotency_key:
            self._by_key[idempotency_key] = ticket_id
        return ticket_id


def ticketing_manifest() -> PluginManifest:
    return PluginManifest(
        id=TICKETING_PLUGIN_ID,
        version="0.1.0",
        publisher_key_id="dula-builtin",
        description="First-party ticketing connector (consequential).",
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
    def __init__(self, backend: TicketBackend) -> None:
        super().__init__(ticketing_manifest())
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
        ticket_id = await self._backend.create(ctx.tenant, title, body, key)
        return ConnectorResult(ok=True, output={"ticket_id": ticket_id})
