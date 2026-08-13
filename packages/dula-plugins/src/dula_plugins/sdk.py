"""Connector SDK (docs/14-Plugins/PluginFramework.md §3).

A small base class connector authors extend: register a handler per capability, and the SDK
dispatches calls, rejects capabilities not in the manifest, and enforces the manifest's output
size limit. Keeps connector code focused on the external system while the SDK + host apply the
uniform safety envelope.
"""

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from typing import Any

from dula_plugins.connector import ConnectorContext, ConnectorResult
from dula_plugins.manifest import PluginManifest

Handler = Callable[[dict[str, Any], ConnectorContext], Awaitable[ConnectorResult]]


class BaseConnector:
    """Base for connectors: dispatch by capability name, enforce manifest + output limits."""

    manifest: PluginManifest

    def __init__(self, manifest: PluginManifest) -> None:
        self.manifest = manifest
        self._handlers: dict[str, Handler] = {}

    def register(self, capability: str, handler: Handler) -> None:
        if self.manifest.capability(capability) is None:
            raise ValueError(f"capability '{capability}' is not declared in the manifest")
        self._handlers[capability] = handler

    async def invoke(
        self, capability: str, args: dict[str, Any], ctx: ConnectorContext
    ) -> ConnectorResult:
        handler = self._handlers.get(capability)
        if handler is None:
            return ConnectorResult(ok=False, error=f"unknown capability '{capability}'")
        result = await handler(args, ctx)
        return self._enforce_output_limit(result)

    def _enforce_output_limit(self, result: ConnectorResult) -> ConnectorResult:
        if not result.ok or result.output is None:
            return result
        try:
            size = len(json.dumps(result.output).encode("utf-8"))
        except (TypeError, ValueError):
            return ConnectorResult(ok=False, error="connector output is not serialisable")
        if size > self.manifest.limits.max_output_bytes:
            return ConnectorResult(
                ok=False,
                error=f"output exceeds limit ({self.manifest.limits.max_output_bytes} bytes)",
            )
        return result
