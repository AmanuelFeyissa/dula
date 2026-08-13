"""Tests for tool contracts and built-in tools."""

from __future__ import annotations

from dula_agents.tools import (
    EnrichIndicatorTool,
    ToolContext,
    default_toolset,
    in_memory_backends,
)
from dula_agents.types import SideEffect

CTX = ToolContext(tenant="t1", subject="u1")


def test_default_toolset_specs() -> None:
    registry = default_toolset(in_memory_backends())
    names = {s.name for s in registry.specs()}
    expected = {"search_logs", "enrich_indicator", "list_alerts", "create_ticket", "isolate_host"}
    assert names == expected
    by_name = {s.name: s for s in registry.specs()}
    assert by_name["search_logs"].side_effect is SideEffect.READ
    assert by_name["create_ticket"].side_effect is SideEffect.CONSEQUENTIAL
    assert by_name["isolate_host"].side_effect is SideEffect.CONSEQUENTIAL


async def test_enrich_indicator_uses_intel_core() -> None:
    tool = EnrichIndicatorTool()
    result = await tool.run({"value": "c2 at evil[.]com and 8.8.8.8"}, CTX)
    assert result.ok and result.untrusted is True
    kinds = {i["kind"] for i in result.output["indicators"]}
    assert {"domain", "ipv4"} <= kinds


async def test_tool_missing_arg_fails_cleanly() -> None:
    tool = EnrichIndicatorTool()
    result = await tool.run({}, CTX)
    assert not result.ok and "missing" in (result.error or "")


async def test_search_logs_is_tenant_scoped() -> None:
    backends = in_memory_backends()
    backends.logs.events["t1"] = [{"host": "HOST-7", "msg": "hit"}]  # type: ignore[attr-defined]
    registry = default_toolset(backends)
    tool = registry.get("search_logs")
    assert tool is not None
    mine = await tool.run({"query": "HOST-7"}, ToolContext("t1", "u1"))
    other = await tool.run({"query": "HOST-7"}, ToolContext("t2", "u1"))
    assert mine.output["count"] == 1
    assert other.output["count"] == 0  # different tenant sees nothing
