"""Unit tests for the declarative playbook core: refs, conditions, bindings, validation."""

from __future__ import annotations

import pytest
from dula_agents.agents import build_investigation_agent
from dula_agents.types import SideEffect, Step, ToolResult
from dula_automation.playbook import (
    Condition,
    Playbook,
    PlaybookError,
    PlaybookStep,
    Ref,
    Template,
    _condition_holds,
    _resolve_args,
    compile_playbook,
    resolve_ref,
    validate_playbook,
)


def _executed(index: int, tool: str, output: object, ok: bool = True) -> Step:
    step = Step(index=index, thought="", tool=tool, args={}, side_effect=SideEffect.READ)
    step.permitted = True
    step.result = ToolResult(ok=ok, output=output)
    return step


def test_resolve_ref_navigates_dicts_and_lists() -> None:
    by_id = {"triage": _executed(0, "list_alerts", {"alerts": [{"indicator": "evil.com"}]})}
    assert resolve_ref(Ref("triage", "alerts.0.indicator"), by_id) == "evil.com"


def test_resolve_ref_returns_default_on_missing_or_failed() -> None:
    by_id = {"triage": _executed(0, "list_alerts", {"alerts": []}, ok=False)}
    assert resolve_ref(Ref("triage", "alerts.0.indicator", default="x"), by_id) == "x"
    assert resolve_ref(Ref("absent", "a.b", default="d"), by_id) == "d"
    ok = {"triage": _executed(0, "list_alerts", {"alerts": []})}
    assert resolve_ref(Ref("triage", "alerts.5.indicator", default="d"), ok) == "d"


def test_template_renders_and_tolerates_missing_refs() -> None:
    by_id = {"triage": _executed(0, "list_alerts", {"alerts": [{"title": "Beacon"}]})}
    tpl = Template("Investigation: {t}", {"t": Ref("triage", "alerts.0.title")})
    assert _resolve_args(
        PlaybookStep(id="x", tool="create_ticket", description="", bind={"title": tpl}), by_id
    ) == {"title": "Investigation: Beacon"}
    empty = Template("v={missing}", {"missing": Ref("absent", "a")})
    step = PlaybookStep(id="x", tool="create_ticket", description="", bind={"b": empty})
    assert _resolve_args(step, {})["b"] == "v="


def test_conditions_gate_on_prior_results() -> None:
    ok = {"triage": _executed(0, "list_alerts", {"alerts": [{"indicator": "evil.com"}]})}
    assert _condition_holds(Condition.always(), {})
    assert _condition_holds(Condition.step_ok("triage"), ok)
    assert not _condition_holds(Condition.step_ok("missing"), ok)
    assert _condition_holds(Condition.ref_nonempty(Ref("triage", "alerts")), ok)
    assert not _condition_holds(Condition.ref_nonempty(Ref("triage", "alerts.0.absent")), ok)
    assert _condition_holds(Condition.ref_truthy(Ref("triage", "alerts.0.indicator")), ok)


def test_validate_rejects_out_of_scope_tool() -> None:
    agent = build_investigation_agent()  # cannot isolate_host
    bad = Playbook(
        name="bad",
        title="",
        description="",
        base_agent=agent.name,
        steps=(PlaybookStep(id="s", tool="isolate_host", description=""),),
    )
    with pytest.raises(PlaybookError, match="outside agent"):
        validate_playbook(bad, agent)


def test_validate_rejects_duplicate_ids_and_forward_refs() -> None:
    agent = build_investigation_agent()
    dup = Playbook(
        name="dup",
        title="",
        description="",
        base_agent=agent.name,
        steps=(
            PlaybookStep(id="a", tool="list_alerts", description=""),
            PlaybookStep(id="a", tool="search_logs", description=""),
        ),
    )
    with pytest.raises(PlaybookError, match="duplicate step id"):
        validate_playbook(dup, agent)

    forward = Playbook(
        name="fwd",
        title="",
        description="",
        base_agent=agent.name,
        steps=(
            PlaybookStep(
                id="a",
                tool="enrich_indicator",
                description="",
                when=Condition.step_ok("later"),
            ),
            PlaybookStep(id="later", tool="list_alerts", description=""),
        ),
    )
    with pytest.raises(PlaybookError, match="not an earlier step"):
        validate_playbook(forward, agent)


def test_compile_inherits_scope_and_limits() -> None:
    agent = build_investigation_agent()
    pb = Playbook(
        name="p",
        title="T",
        description="d",
        base_agent=agent.name,
        steps=(PlaybookStep(id="a", tool="list_alerts", description=""),),
    )
    compiled = compile_playbook(pb, agent)
    assert compiled.name == "p"
    assert compiled.scope is agent.scope
    assert compiled.limits is agent.limits
