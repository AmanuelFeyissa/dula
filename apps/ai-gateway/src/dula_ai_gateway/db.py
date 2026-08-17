"""Async database engine/session helpers (ADR-0016).

Mirrors ``dula_platform_api.db``'s ``make_engine``/``make_sessionmaker`` naming and shape. The
AI Gateway has no per-request DB dependency the way platform-api does — ``PostgresRunStore``
opens and scopes its own short-lived sessions per call (see ``run_store_postgres.py``) — so
this module only builds the shared engine/sessionmaker once at startup.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def make_engine(database_url: str) -> AsyncEngine:
    """Create the async engine (does not connect until first use)."""
    return create_async_engine(database_url, pool_pre_ping=True, future=True)


def make_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
