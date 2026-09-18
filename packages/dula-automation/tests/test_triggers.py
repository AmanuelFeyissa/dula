"""Scheduled / event-triggered playbooks: delegation semantics, due logic, tenant scoping."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field

import pytest
from dula_agents.types import RunRecord
from dula_automation.triggers import (
    InMemoryTriggerStore,
    TriggerError,
    TriggerService,
)


@dataclass
class _RecordingRunner:
    started: list[dict[str, object]] = field(default_factory=list)
    fail: bool = False

    async def start_playbook(
        self, *, playbook: str, goal: str, tenant: str, subject: str, roles: tuple[str, ...]
    ) -> RunRecord:
        if self.fail:
            raise RuntimeError("runtime unavailable")
        self.started.append(
            {
                "playbook": playbook,
                "goal": goal,
                "tenant": tenant,
                "subject": subject,
                "roles": roles,
            }
        )
        return RunRecord(
            run_id=f"run-{len(self.started)}",
            agent=playbook,
            goal=goal,
            tenant=tenant,
            subject=subject,
        )


class _Clock:
    def __init__(self, start: dt.datetime) -> None:
        self.now = start

    def __call__(self) -> dt.datetime:
        return self.now

    def advance(self, seconds: int) -> None:
        self.now = self.now + dt.timedelta(seconds=seconds)


T0 = dt.datetime(2026, 9, 18, 12, 0, tzinfo=dt.UTC)


def _service(
    runner: _RecordingRunner | None = None,
) -> tuple[TriggerService, _RecordingRunner, _Clock]:
    runner = runner or _RecordingRunner()
    clock = _Clock(T0)
    return TriggerService(InMemoryTriggerStore(), runner, clock=clock), runner, clock


async def test_create_requires_exactly_one_kind_and_a_sane_interval() -> None:
    svc, _, _ = _service()
    with pytest.raises(TriggerError):
        await svc.create(tenant="t1", playbook="p", subject="maya", roles=("analyst",), goal="g")
    with pytest.raises(TriggerError):
        await svc.create(
            tenant="t1",
            playbook="p",
            subject="maya",
            roles=("analyst",),
            goal="g",
            interval_seconds=600,
            event_type="alert.created",
        )
    with pytest.raises(TriggerError):
        await svc.create(
            tenant="t1",
            playbook="p",
            subject="maya",
            roles=("analyst",),
            goal="g",
            interval_seconds=5,
        )


async def test_interval_trigger_fires_when_due_on_behalf_of_creator() -> None:
    svc, runner, clock = _service()
    trigger = await svc.create(
        tenant="t1",
        playbook="triage-enrich-ticket",
        subject="maya",
        roles=("analyst",),
        goal="Hourly triage sweep",
        interval_seconds=3600,
    )
    assert trigger.kind == "interval" and trigger.next_fire_at == T0 + dt.timedelta(hours=1)

    assert await svc.tick() == []  # not due yet
    clock.advance(3600)
    started = await svc.tick()
    assert len(started) == 1 and runner.started[0] == {
        "playbook": "triage-enrich-ticket",
        "goal": "Hourly triage sweep",
        "tenant": "t1",
        "subject": "maya",
        "roles": ("analyst",),
    }
    assert await svc.tick() == []  # advanced, not re-fired in the same window
    stored = (await svc._store.for_tenant("t1"))[0]
    assert stored.fire_count == 1 and stored.next_fire_at == clock.now + dt.timedelta(hours=1)


async def test_event_trigger_matches_tenant_and_type_only() -> None:
    svc, runner, _ = _service()
    await svc.create(
        tenant="t1",
        playbook="triage-enrich-ticket",
        subject="maya",
        roles=("analyst",),
        goal="Triage new alert",
        event_type="alert.created",
    )
    other_tenant = await svc.on_event(
        event_type="alert.created", tenant="t2", event={"type": "alert.created", "id": "e1"}
    )
    other_type = await svc.on_event(
        event_type="incident.created", tenant="t1", event={"type": "incident.created", "id": "e2"}
    )
    assert other_tenant == [] and other_type == []

    started = await svc.on_event(
        event_type="alert.created",
        tenant="t1",
        event={"type": "alert.created", "id": "e3", "data": {"ignored": "payload"}},
    )
    assert len(started) == 1
    assert runner.started[0]["goal"] == "Triage new alert [event alert.created e3]"
    assert "payload" not in str(runner.started[0]["goal"])


async def test_disabled_trigger_never_fires_and_is_tenant_scoped() -> None:
    svc, runner, clock = _service()
    trigger = await svc.create(
        tenant="t1", playbook="p", subject="maya", roles=("analyst",), goal="g", interval_seconds=60
    )
    assert await svc.disable("t2", trigger.trigger_id) is None  # another tenant can't touch it
    assert (await svc.disable("t1", trigger.trigger_id)) is not None
    clock.advance(600)
    assert await svc.tick() == [] and runner.started == []


async def test_a_failing_start_does_not_break_the_tick_for_other_triggers() -> None:
    svc, runner, clock = _service()
    await svc.create(
        tenant="t1", playbook="p", subject="maya", roles=("analyst",), goal="g", interval_seconds=60
    )
    runner.fail = True
    clock.advance(120)
    assert await svc.tick() == []  # logged, not raised
    runner.fail = False
    assert len(await svc.tick()) == 1  # still due: the failed attempt did not advance it
