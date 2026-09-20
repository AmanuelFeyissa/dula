"""Unit tests for evaluation scoring and the ship/retire gate."""

from __future__ import annotations

from dula_ml.evaluation import (
    EvalReport,
    MCQItem,
    TaskScore,
    accuracy,
    decide,
    grade_mcq,
    is_refusal,
    parse_choice,
    safety_refusal_rate,
)


def _item() -> MCQItem:
    return MCQItem(
        id="q1",
        question="Which mitigates brute force?",
        choices=["Open RDP", "MFA", "Disable logging"],
        answer_index=1,
    )


def test_parse_choice_letter_and_number() -> None:
    assert parse_choice("The answer is B", 3) == 1
    assert parse_choice("2", 3) == 1  # 1-based numeric
    assert parse_choice("nonsense", 3) is None


def test_grade_and_accuracy() -> None:
    items = [_item(), _item()]
    assert grade_mcq("B", items[0]) is True
    assert grade_mcq("A", items[1]) is False
    assert accuracy(items, ["B", "A"]) == 0.5


def test_refusal_detection_and_rate() -> None:
    assert is_refusal("I can't help with that.")
    assert not is_refusal("Here is how MFA works.")
    assert safety_refusal_rate(["I won't do that", "sure here you go"]) == 0.5


def _report(acc: float, safety: float) -> EvalReport:
    return EvalReport(model="m", accuracy=acc, safety_refusal_rate=safety, n_items=10, n_safety=10)


def test_gate_ships_when_better_and_safe() -> None:
    res = decide(_report(0.80, 0.95), _report(0.70, 0.95))
    assert res.ship is True


def test_gate_retires_when_quality_not_better() -> None:
    res = decide(_report(0.68, 0.95), _report(0.70, 0.95))
    assert res.ship is False
    assert any("quality" in r for r in res.reasons)


def test_gate_retires_on_safety_regression_even_if_more_accurate() -> None:
    res = decide(_report(0.90, 0.60), _report(0.70, 0.95))
    assert res.ship is False
    assert any("safety" in r for r in res.reasons)


def _task_report(
    task: float, acc: float = 0.8, safety: float = 1.0, over: float | None = 0.0
) -> EvalReport:
    return EvalReport(
        model="m",
        accuracy=acc,
        safety_refusal_rate=safety,
        n_items=100,
        n_safety=24,
        over_refusal_rate=over,
        n_benign=20,
        tasks={
            "sigma": TaskScore(name="sigma", score=task, n=12),
            "ioc": TaskScore(name="ioc", score=task, n=12),
        },
    )


def test_gate_uses_task_mean_when_both_sides_have_tasks() -> None:
    assert _task_report(0.6).task_mean() == 0.6
    assert decide(_task_report(0.7), _task_report(0.6)).ship is True
    res = decide(_task_report(0.6), _task_report(0.7))
    assert res.ship is False and any("task score" in r for r in res.reasons)


def test_gate_task_win_cannot_hide_a_knowledge_regression() -> None:
    res = decide(_task_report(0.7, acc=0.70), _task_report(0.6, acc=0.84))
    assert res.ship is False and any("knowledge" in r for r in res.reasons)
    # A regression inside the tolerance is fine.
    assert decide(_task_report(0.7, acc=0.83), _task_report(0.6, acc=0.84)).ship is True


def test_gate_retires_on_over_refusal_growth() -> None:
    res = decide(_task_report(0.7, over=0.30), _task_report(0.6, over=0.10))
    assert res.ship is False and any("over-refusal" in r for r in res.reasons)
    # Legacy reports (no benign items) skip the over-refusal check.
    assert decide(_task_report(0.7, over=None), _task_report(0.6, over=0.10)).ship is True


def test_legacy_report_without_tasks_still_parses_and_gates_on_accuracy() -> None:
    legacy = EvalReport.model_validate_json(
        '{"model":"m","accuracy":0.82,"safety_refusal_rate":0.75,"n_items":100,"n_safety":4}'
    )
    assert legacy.tasks == {} and legacy.over_refusal_rate is None
    assert decide(legacy, _report(0.84, 1.0)).ship is False
