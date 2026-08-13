"""Run persistence (docs/13-Agents/AgentLifecycle.md §2).

Agent runs pause for approval and resume across requests, so the run record outlives a single
call and must be stored. The in-memory store here is tenant-scoped (a run is only ever returned
to its owning tenant — never cross-tenant, ADR-0006) and retains the invoker's roles so a
resumed run keeps acting as the original user. Production swaps this for a durable store behind
the same interface.
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
    def save(self, record: RunRecord, roles: tuple[str, ...]) -> None: ...

    def get(self, tenant: str, run_id: str) -> StoredRun | None: ...


@dataclass
class InMemoryRunStore:
    _runs: dict[str, StoredRun] = field(default_factory=dict)

    def save(self, record: RunRecord, roles: tuple[str, ...]) -> None:
        self._runs[record.run_id] = StoredRun(record=record, roles=roles)

    def get(self, tenant: str, run_id: str) -> StoredRun | None:
        stored = self._runs.get(run_id)
        # Tenant isolation: never return a run to a tenant that does not own it.
        if stored is None or stored.record.tenant != tenant:
            return None
        return stored
