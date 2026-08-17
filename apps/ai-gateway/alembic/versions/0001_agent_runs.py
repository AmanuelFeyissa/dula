"""agent runs: durable agent/playbook run persistence (+ RLS per ADR-0006, ADR-0016)

Revision ID: 0001_agent_runs
Revises:
Create Date: 2026-08-17
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_agent_runs"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# tenant_id is not a foreign key to platform-api's `tenants` table on purpose: the two
# services run independent migration chains against the same database, and a cross-service
# FK would make this chain depend on platform-api's migrations having already run first
# (models.py explains the reasoning in full). RLS still applies the same way it does to the
# domain spine (migration 0002_domain_spine.py in platform-api).
_TENANT_TABLES = ("agent_runs", "agent_run_steps")


def upgrade() -> None:
    op.create_table(
        "agent_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("agent", sa.String(128), nullable=False),
        sa.Column("goal", sa.String(2000), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("roles", postgresql.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("state", sa.String(32), nullable=False),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_agent_runs_tenant_id", "agent_runs", ["tenant_id"])

    op.create_table(
        "agent_run_steps",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agent_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("thought", sa.Text(), nullable=False, server_default=""),
        sa.Column("tool", sa.String(128), nullable=False),
        sa.Column("args", postgresql.JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("side_effect", sa.String(16), nullable=False),
        sa.Column("permitted", sa.Boolean(), nullable=True),
        sa.Column("permission_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("approved", sa.Boolean(), nullable=True),
        sa.Column("approver", sa.String(255), nullable=True),
        sa.Column("approver_username", sa.String(255), nullable=True),
        sa.Column("approval_reason", sa.Text(), nullable=False, server_default=""),
        sa.Column("result_ok", sa.Boolean(), nullable=True),
        sa.Column("result_output", postgresql.JSONB, nullable=True),
        sa.Column("result_error", sa.Text(), nullable=True),
    )
    op.create_index("ix_agent_run_steps_run_id", "agent_run_steps", ["run_id"])
    op.create_index("ix_agent_run_steps_tenant_id", "agent_run_steps", ["tenant_id"])

    for table in _TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY {table}_tenant_isolation ON {table} "
            "USING (tenant_id = current_setting('app.current_tenant', true)::uuid)"
        )


def downgrade() -> None:
    for table in _TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}")

    op.drop_index("ix_agent_run_steps_tenant_id", table_name="agent_run_steps")
    op.drop_index("ix_agent_run_steps_run_id", table_name="agent_run_steps")
    op.drop_table("agent_run_steps")
    op.drop_index("ix_agent_runs_tenant_id", table_name="agent_runs")
    op.drop_table("agent_runs")
