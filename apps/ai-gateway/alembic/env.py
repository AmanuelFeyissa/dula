"""Alembic async migration environment (docs/07-Database/MigrationStrategy.md, ADR-0016)."""

from __future__ import annotations

import asyncio

from alembic import context
from dula_ai_gateway.config import get_settings
from dula_ai_gateway.models import Base
from sqlalchemy import Connection
from sqlalchemy.ext.asyncio import create_async_engine

config = context.config
target_metadata = Base.metadata

# The AI Gateway and platform-api run independent migration chains against the *same*
# database (models.py explains why agent_runs.tenant_id isn't an FK to platform-api's
# tenants table). Alembic's default `alembic_version` table is shared per-database, so
# without a distinct name here, this chain collides with platform-api's the moment both
# have run once — each stamps a revision id the other's chain has never heard of.
VERSION_TABLE = "dula_ai_gateway_alembic_version"


def _run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection, target_metadata=target_metadata, version_table=VERSION_TABLE
    )
    with context.begin_transaction():
        context.run_migrations()


async def _run_async() -> None:
    engine = create_async_engine(get_settings().database_url, future=True)
    async with engine.connect() as connection:
        await connection.run_sync(_run_migrations)
    await engine.dispose()


def run_migrations_offline() -> None:
    context.configure(
        url=get_settings().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table=VERSION_TABLE,
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(_run_async())
