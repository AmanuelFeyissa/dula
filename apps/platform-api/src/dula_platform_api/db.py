"""Async database engine/session helpers (docs/07-Database/DatabaseArchitecture.md)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from dula_platform_api.deps import Context


def make_engine(database_url: str) -> AsyncEngine:
    """Create the async engine (does not connect until first use)."""
    return create_async_engine(database_url, pool_pre_ping=True, future=True)


def make_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a request-scoped session (no tenant scoping)."""
    maker: async_sessionmaker[AsyncSession] = request.app.state.sessionmaker
    async with maker() as session:
        yield session


async def get_tenant_session(request: Request, ctx: Context) -> AsyncIterator[AsyncSession]:
    """Yield a session bound to the caller's tenant for the connection's lifetime.

    Sets the ``app.current_tenant`` GUC that the RLS policies read (ADR-0006). The value
    is reset on teardown so a pooled connection never carries one tenant's scope into the
    next request (a cross-tenant leak). Repositories additionally filter by ``tenant_id``.
    """
    maker: async_sessionmaker[AsyncSession] = request.app.state.sessionmaker
    async with maker() as session:
        await session.execute(
            text("SELECT set_config('app.current_tenant', :tid, false)"),
            {"tid": str(ctx.tenant_id)},
        )
        try:
            yield session
        finally:
            await session.execute(text("SELECT set_config('app.current_tenant', '', false)"))


TenantSession = Annotated[AsyncSession, Depends(get_tenant_session)]
