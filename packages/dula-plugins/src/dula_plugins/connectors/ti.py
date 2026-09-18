"""Threat-intel connector (`ti.lookup_indicator` read; `ti.live_lookup` egress-gated read).

`ti.lookup_indicator` enriches a value **offline**: it extracts indicators with the Phase 05
intel core and scores them against a local reputation fixture — always available, air-gapped.
`ti.live_lookup` represents an external feed lookup; it must pass the **egress guard**, so it is
**inert in air-gapped installs** (no hidden phone-home) and only works where egress to the
declared feed host is permitted. Prefer open standards (STIX) for real feeds.
"""

from __future__ import annotations

from typing import Any

import httpx
from dula_ai.intel.iocs import extract

from dula_plugins.connector import ConnectorContext, ConnectorResult
from dula_plugins.egress import EgressError
from dula_plugins.http import EgressHttpClient, HttpError, auth_headers
from dula_plugins.manifest import Capability, PluginManifest, SideEffect
from dula_plugins.sdk import BaseConnector

TI_PLUGIN_ID = "dula-plugin-dula-ti"
TI_FEED_HOST = "ti.example.com"  # placeholder; deployments configure the real feed host
TI_FEED_PATH = "/api/v1/lookup"
TI_SECRET_KEY = "ti.authorization"  # noqa: S105 - the secret's *name*; value is in the provider

# Offline reputation fixture (normalized). Real deployments use a STIX/TAXII feed via egress.
_REPUTATION: dict[str, str] = {
    "evil.example.com": "malicious",
    "evil.com": "malicious",
    "198.51.100.23": "suspicious",
    "203.0.113.9": "malicious",
}


def ti_manifest(feed_host: str = TI_FEED_HOST) -> PluginManifest:
    return PluginManifest(
        id=TI_PLUGIN_ID,
        version="0.2.0",
        publisher_key_id="dula-builtin",
        description="First-party threat-intel lookup connector.",
        egress=[feed_host],
        capabilities=[
            Capability(
                name="ti.lookup_indicator",
                side_effect=SideEffect.READ,
                permission="connector.ti.lookup",
                description="Offline reputation + IOC extraction for a value.",
            ),
            Capability(
                name="ti.live_lookup",
                side_effect=SideEffect.READ,
                permission="connector.ti.live_lookup",
                description="External feed lookup (requires egress; inert air-gapped).",
                requires_egress=True,
            ),
        ],
    )


def _score(value: str) -> dict[str, Any]:
    rep = _REPUTATION.get(value.lower(), "unknown")
    return {
        "value": value,
        "reputation": rep,
        "sources": ["dula-fixture"] if rep != "unknown" else [],
    }


class ThreatIntelConnector(BaseConnector):
    def __init__(
        self,
        *,
        feed_host: str = TI_FEED_HOST,
        feed_path: str = TI_FEED_PATH,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        super().__init__(ti_manifest(feed_host))
        self._feed_host = feed_host
        self._feed_path = feed_path
        self._transport = transport
        self.register("ti.lookup_indicator", self._lookup)
        self.register("ti.live_lookup", self._live_lookup)

    async def _lookup(self, args: dict[str, Any], ctx: ConnectorContext) -> ConnectorResult:
        value = args.get("value")
        if not isinstance(value, str) or not value.strip():
            return ConnectorResult(ok=False, error="missing 'value'")
        indicators = [
            {"kind": i.kind, "value": i.value, "defanged": i.defanged, **_score(i.value)}
            for i in extract(value)
        ]
        # Also score the raw value directly (e.g. a bare domain the extractor normalises).
        if not indicators:
            indicators = [{"kind": "raw", "defanged": value, **_score(value)}]
        return ConnectorResult(ok=True, output={"indicators": indicators})

    async def _live_lookup(self, args: dict[str, Any], ctx: ConnectorContext) -> ConnectorResult:
        value = args.get("value")
        if not isinstance(value, str) or not value.strip():
            return ConnectorResult(ok=False, error="missing 'value'")
        url = f"https://{self._feed_host}{self._feed_path}"
        client = EgressHttpClient(ctx.egress, transport=self._transport or ctx.transport)
        try:
            # The guard inside the client is the gate: air-gapped / undeclared host → denied.
            data = await client.get_json(
                url,
                params={"indicator": value},
                headers=auth_headers(ctx.secrets.get(TI_SECRET_KEY)),
            )
        except EgressError as exc:
            return ConnectorResult(ok=False, error=f"egress denied: {exc}")
        except HttpError as exc:
            return ConnectorResult(ok=False, error=f"feed request failed: {exc}")
        return ConnectorResult(
            ok=True,
            output={"value": value, "feed": self._feed_host, "live": True, "response": data},
        )
