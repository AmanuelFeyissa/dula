"""Scheduled and event-triggered playbook runs (docs/13-Agents/Playbooks.md).

A trigger starts a playbook run without a person at the keyboard -- either on a fixed
interval or when a domain event of a given type arrives for the tenant. What does *not*
change is the security model: the run is started **on behalf of the analyst who created the
trigger**, with that person's roles snapshotted at creation time, so it can do no more than
they could (agent ⊆ user); and a consequential step still stops for human approval -- a
scheduled run never approves itself. A trigger is therefore a standing, revocable delegation,
and the store is tenant-scoped like everything else.
"""

from __future__ import annotations

import asyncio
import contextlib
import datetime as dt
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import Any, Protocol

from dula_agents.types import RunRecord

_log = logging.getLogger(__name__)

MIN_INTERVAL_SECONDS = 60


class TriggerError(ValueError):
    """Invalid trigger definition."""


@dataclass(frozen=True, slots=True)
class Trigger:
    trigger_id: str
    tenant: str
    playbook: str
    subject: str  # the person the runs act on behalf of
    roles: tuple[str, ...]  # their roles, snapshotted when the trigger was created
    goal: str
    interval_seconds: int | None = None
    event_type: str | None = None
    enabled: bool = True
    created_at: dt.datetime = field(default_factory=lambda: dt.datetime.now(dt.UTC))
    next_fire_at: dt.datetime | None = None
    last_fired_at: dt.datetime | None = None
    fire_count: int = 0

    @property
    def kind(self) -> str:
        return "interval" if self.interval_seconds is not None else "event"


class TriggerStore(Protocol):
    async def save(self, trigger: Trigger) -> None: ...

    async def get(self, tenant: str, trigger_id: str) -> Trigger | None: ...

    async def for_tenant(self, tenant: str) -> list[Trigger]: ...

    async def enabled(self) -> list[Trigger]: ...


@dataclass
class InMemoryTriggerStore:
    _triggers: dict[str, Trigger] = field(default_factory=dict)

    async def save(self, trigger: Trigger) -> None:
        self._triggers[trigger.trigger_id] = trigger

    async def get(self, tenant: str, trigger_id: str) -> Trigger | None:
        t = self._triggers.get(trigger_id)
        return t if t is not None and t.tenant == tenant else None

    async def for_tenant(self, tenant: str) -> list[Trigger]:
        return sorted(
            (t for t in self._triggers.values() if t.tenant == tenant), key=lambda t: t.created_at
        )

    async def enabled(self) -> list[Trigger]:
        return [t for t in self._triggers.values() if t.enabled]


class PlaybookRunner(Protocol):
    """Starts a playbook run exactly the way the API does (compile → runtime → store)."""

    async def start_playbook(
        self, *, playbook: str, goal: str, tenant: str, subject: str, roles: tuple[str, ...]
    ) -> RunRecord: ...


Clock = Callable[[], dt.datetime]


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.UTC)


class TriggerService:
    def __init__(self, store: TriggerStore, runner: PlaybookRunner, *, clock: Clock = _utcnow):
        self._store = store
        self._runner = runner
        self._clock = clock

    async def create(
        self,
        *,
        tenant: str,
        playbook: str,
        subject: str,
        roles: tuple[str, ...],
        goal: str,
        interval_seconds: int | None = None,
        event_type: str | None = None,
    ) -> Trigger:
        if (interval_seconds is None) == (event_type is None):
            raise TriggerError("set exactly one of interval_seconds or event_type")
        if interval_seconds is not None and interval_seconds < MIN_INTERVAL_SECONDS:
            raise TriggerError(f"interval_seconds must be >= {MIN_INTERVAL_SECONDS}")
        if event_type is not None and not event_type.strip():
            raise TriggerError("event_type must not be empty")
        now = self._clock()
        trigger = Trigger(
            trigger_id=f"trg-{uuid.uuid4().hex[:12]}",
            tenant=tenant,
            playbook=playbook,
            subject=subject,
            roles=tuple(roles),
            goal=goal.strip() or f"Run playbook '{playbook}'",
            interval_seconds=interval_seconds,
            event_type=event_type.strip() if event_type else None,
            created_at=now,
            next_fire_at=(
                now + dt.timedelta(seconds=interval_seconds) if interval_seconds else None
            ),
        )
        await self._store.save(trigger)
        return trigger

    async def get(self, tenant: str, trigger_id: str) -> Trigger | None:
        return await self._store.get(tenant, trigger_id)

    async def for_tenant(self, tenant: str) -> list[Trigger]:
        return await self._store.for_tenant(tenant)

    async def disable(self, tenant: str, trigger_id: str) -> Trigger | None:
        trigger = await self._store.get(tenant, trigger_id)
        if trigger is None:
            return None
        trigger = replace(trigger, enabled=False, next_fire_at=None)
        await self._store.save(trigger)
        return trigger

    async def fire(self, trigger: Trigger, *, event: dict[str, Any] | None = None) -> RunRecord:
        """Start one run for the trigger, on behalf of its creator, and advance its schedule."""
        goal = trigger.goal
        if event is not None:
            # Only the event's identity reaches the goal; its payload is untrusted data the
            # playbook's tools fetch through their own permissioned paths.
            goal = f"{goal} [event {event.get('type', '?')} {event.get('id', '')}]".rstrip()
        record = await self._runner.start_playbook(
            playbook=trigger.playbook,
            goal=goal,
            tenant=trigger.tenant,
            subject=trigger.subject,
            roles=trigger.roles,
        )
        now = self._clock()
        await self._store.save(
            replace(
                trigger,
                last_fired_at=now,
                fire_count=trigger.fire_count + 1,
                next_fire_at=(
                    now + dt.timedelta(seconds=trigger.interval_seconds)
                    if trigger.interval_seconds
                    else None
                ),
            )
        )
        return record

    async def tick(self, now: dt.datetime | None = None) -> list[RunRecord]:
        """Fire every enabled interval trigger that is due. Safe to call often."""
        now = now or self._clock()
        started: list[RunRecord] = []
        for trigger in await self._store.enabled():
            if trigger.next_fire_at is None or trigger.next_fire_at > now:
                continue
            try:
                started.append(await self.fire(trigger))
            except Exception:
                _log.exception(
                    "scheduled playbook failed to start",
                    extra={"trigger": trigger.trigger_id, "tenant": trigger.tenant},
                )
        return started

    async def on_event(
        self, *, event_type: str, tenant: str, event: dict[str, Any]
    ) -> list[RunRecord]:
        """Fire every enabled trigger for this tenant that subscribes to ``event_type``."""
        started: list[RunRecord] = []
        for trigger in await self._store.enabled():
            if trigger.tenant != tenant or trigger.event_type != event_type:
                continue
            try:
                started.append(await self.fire(trigger, event=event))
            except Exception:
                _log.exception(
                    "event-triggered playbook failed to start",
                    extra={"trigger": trigger.trigger_id, "tenant": tenant, "event": event_type},
                )
        return started


class Scheduler:
    """Background loop calling ``TriggerService.tick`` every ``tick_seconds``."""

    def __init__(self, service: TriggerService, *, tick_seconds: float = 15.0) -> None:
        self._service = service
        self._tick = tick_seconds
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._loop(), name="dula-automation-scheduler")

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _loop(self) -> None:
        while True:
            await asyncio.sleep(self._tick)
            try:
                await self._service.tick()
            except Exception:  # keep the loop alive; individual failures are logged in tick()
                _log.exception("scheduler tick failed")
