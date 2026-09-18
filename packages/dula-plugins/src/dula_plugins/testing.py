"""A probe connector for exercising sandbox runners (tests and operator self-checks).

It never touches the network; each capability reports one thing about the environment the
connector runs in, so a runner's isolation claims can be checked from the outside: another
PID, no secret values, a wall-time kill, a crash surfaced as a failed result. It lives in the
package (not in ``tests/``) because the out-of-process runner has to import it by name in a
fresh interpreter.
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

from dula_plugins.connector import ConnectorContext, ConnectorResult
from dula_plugins.manifest import Capability, PluginManifest, SideEffect
from dula_plugins.sdk import BaseConnector

PROBE_PLUGIN_ID = "dula-plugin-dula-probe"


def probe_manifest() -> PluginManifest:
    return PluginManifest(
        id=PROBE_PLUGIN_ID,
        version="0.1.0",
        publisher_key_id="dula-builtin",
        description="Sandbox probe: reports the worker's PID, secret visibility, timing.",
        capabilities=[
            Capability(name="probe.pid", side_effect=SideEffect.READ, permission="probe.read"),
            Capability(name="probe.sleep", side_effect=SideEffect.READ, permission="probe.read"),
            Capability(name="probe.crash", side_effect=SideEffect.READ, permission="probe.read"),
            Capability(name="probe.secret", side_effect=SideEffect.READ, permission="probe.read"),
        ],
    )


class ProbeConnector(BaseConnector):
    def __init__(self) -> None:
        super().__init__(probe_manifest())
        self.register("probe.pid", self._pid)
        self.register("probe.sleep", self._sleep)
        self.register("probe.crash", self._crash)
        self.register("probe.secret", self._secret)

    async def _pid(self, args: dict[str, Any], ctx: ConnectorContext) -> ConnectorResult:
        return ConnectorResult(ok=True, output={"pid": os.getpid()})

    async def _sleep(self, args: dict[str, Any], ctx: ConnectorContext) -> ConnectorResult:
        await asyncio.sleep(float(args.get("seconds", 30)))
        return ConnectorResult(ok=True, output={"slept": True})

    async def _crash(self, args: dict[str, Any], ctx: ConnectorContext) -> ConnectorResult:
        raise RuntimeError("boom")

    async def _secret(self, args: dict[str, Any], ctx: ConnectorContext) -> ConnectorResult:
        key = str(args.get("key", "probe.secret"))
        return ConnectorResult(ok=True, output={"seen": ctx.secrets.get(key)})
