"""Run persistence (docs/13-Agents/AgentLifecycle.md §2, ADR-0016).

Agent runs pause for approval and resume across requests, so the run record outlives a single
call and must be stored. ``RunStore`` is async so a durable (Postgres) implementation can sit
behind the same interface as the in-memory one — see ``PostgresRunStore`` in the AI Gateway
(ADR-0016). The in-memory store here is tenant-scoped (a run is only ever returned to its
owning tenant — never cross-tenant, ADR-0006) and retains the invoker's roles so a resumed run
keeps acting as the original user.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from dula_agents.types import RunRecord


@dataclass(frozen=True, slots=True)
class StoredRun:
    record: RunRecord
    roles: tuple[str, ...]  # the invoking user's roles, for safe resume


class RunStore(Protocol):
    async def save(self, record: RunRecord, roles: tuple[str, ...]) -> None: ...

    async def get(self, tenant: str, run_id: str) -> StoredRun | None: ...


@dataclass
class InMemoryRunStore:
    _runs: dict[str, StoredRun] = field(default_factory=dict)

    async def save(self, record: RunRecord, roles: tuple[str, ...]) -> None:
        self._runs[record.run_id] = StoredRun(record=record, roles=roles)

    async def get(self, tenant: str, run_id: str) -> StoredRun | None:
        stored = self._runs.get(run_id)
        # Tenant isolation: never return a run to a tenant that does not own it.
        if stored is None or stored.record.tenant != tenant:
            return None
        return stored
