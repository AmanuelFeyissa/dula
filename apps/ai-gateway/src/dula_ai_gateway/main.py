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
from dula_ai_gateway.config import Settings, get_settings
from dula_ai_gateway.routers import agents, ask, health, intel, knowledge, triage
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
    app.state.agents = build_agent_subsystem(app.state.opa)
    try:
        yield
    finally:
        await publisher.stop()


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
    return app


app = create_app()
