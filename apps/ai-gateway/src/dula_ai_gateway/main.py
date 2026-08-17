"""AI Gateway application factory."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dula_ai.gateway import AuditRecord
from dula_common.events import EventEnvelope, EventPublisher
from dula_common.logging import configure_logging
from dula_common.opa import OPAClient
from dula_common.telemetry import setup_telemetry
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dula_ai_gateway.agents_wiring import build_agent_subsystem
from dula_ai_gateway.automation_wiring import build_automation_subsystem
from dula_ai_gateway.config import Settings, get_settings
from dula_ai_gateway.db import make_engine, make_sessionmaker
from dula_ai_gateway.plugins_wiring import build_plugins_subsystem
from dula_ai_gateway.routers import (
    agents,
    ask,
    automation,
    health,
    intel,
    knowledge,
    plugins,
    triage,
)
from dula_ai_gateway.run_store_postgres import PostgresRunStore
from dula_ai_gateway.wiring import build_subsystem

_log = logging.getLogger(__name__)


def _make_audit_hook(publisher: EventPublisher):  # type: ignore[no-untyped-def]
    async def audit(rec: AuditRecord) -> None:
        # AI-call audit: structured log (Loki) + a domain event (bus). No prompt content is
        # logged — only metadata (T5/T13: no sensitive content in audit).
        _log.info(
            "ai call",
            extra={
                "tenant": rec.tenant,
                "subject": rec.subject,
                "task": rec.task,
                "model": rec.model,
                "tokens": rec.usage.total_tokens,
                "cached": rec.cached,
                "input_flags": rec.input_flags,
            },
        )
        await publisher.publish(
            EventEnvelope(
                type="ai.query.completed",
                tenant_id=rec.tenant,
                data={
                    "task": rec.task,
                    "model": rec.model,
                    "tokens": rec.usage.total_tokens,
                    "cached": rec.cached,
                    "actor": rec.subject,
                    "flags": rec.input_flags,
                },
            )
        )

    return audit


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    publisher = EventPublisher(
        settings.kafka_bootstrap_servers,
        topic=settings.events_topic,
        enabled=settings.events_enabled,
    )
    await publisher.start()
    app.state.publisher = publisher
    app.state.opa = OPAClient(settings.opa_url)
    app.state.subsystem = await build_subsystem(settings, _make_audit_hook(publisher))
    app.state.plugins = build_plugins_subsystem(
        app.state.opa, egress_enabled=settings.plugins_egress_enabled
    )

    # Agent/playbook run persistence (ADR-0016). "memory" (the default) needs no Postgres at
    # all — the offline/air-gapped path is unchanged. "postgres" makes runs and their
    # approvals survive a restart, using the same database as platform-api with its own
    # migration chain and tables (agent_runs, agent_run_steps).
    engine = None
    agent_store = None
    automation_store = None
    if settings.run_store == "postgres":
        engine = make_engine(settings.database_url)
        sessionmaker = make_sessionmaker(engine)
        agent_store = PostgresRunStore(sessionmaker, kind="agent")
        automation_store = PostgresRunStore(sessionmaker, kind="automation")
    app.state.db_engine = engine

    app.state.agents = build_agent_subsystem(app.state.opa, app.state.plugins, store=agent_store)
    app.state.automation = build_automation_subsystem(app.state.agents, store=automation_store)
    try:
        yield
    finally:
        await publisher.stop()
        if engine is not None:
            await engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    setup_telemetry(settings.service_name)

    app = FastAPI(title="Dula AI Gateway", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(ask.router)
    app.include_router(triage.router)
    app.include_router(knowledge.router)
    app.include_router(intel.router)
    app.include_router(agents.router)
    app.include_router(plugins.router)
    app.include_router(automation.router)
    return app


app = create_app()
