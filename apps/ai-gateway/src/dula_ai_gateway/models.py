"""ORM models for durable agent/playbook run persistence (ADR-0016).

One physical table pair backs both the agent subsystem and the automation subsystem — a
playbook run *is* an agent run (automation_wiring.py) — disambiguated by ``kind`` so the two
run pools stay logically separate, matching today's separate in-memory stores. ``tenant_id``
is not a foreign key to the platform-api ``tenants`` table on purpose: the two services run
independent migration chains against the same database, and a cross-service FK would make
each service's migrations depend on the other's having already run. The tenant claim is
already authenticated and authorized upstream (OIDC + OPA); the column just carries it, and
RLS (below) plus the repository-level filter in ``run_store_postgres.py`` enforce isolation
the same way ADR-0006 requires for the domain spine.
"""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AgentRun(Base):
    __tablename__ = "agent_runs"

    # The run's own id (dula_agents.runtime generates `uuid.uuid4().hex`; the run_store
    # coerces to/from this UUID column at the boundary — see run_store_postgres.py).
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(16), nullable=False)  # "agent" | "automation"
    agent: Mapped[str] = mapped_column(String(128), nullable=False)
    goal: Mapped[str] = mapped_column(String(2000), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    roles: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    state: Mapped[str] = mapped_column(String(32), nullable=False)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )


class AgentRunStep(Base):
    __tablename__ = "agent_run_steps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Denormalized from the parent run so RLS can scope this table too without a join.
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    thought: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tool: Mapped[str] = mapped_column(String(128), nullable=False)
    args: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    side_effect: Mapped[str] = mapped_column(String(16), nullable=False)
    permitted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    permission_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    approved: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    approver: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approver_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approval_reason: Mapped[str] = mapped_column(Text, nullable=False, default="")
    result_ok: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    result_output: Mapped[Any] = mapped_column(JSONB, nullable=True)
    result_error: Mapped[str | None] = mapped_column(Text, nullable=True)
