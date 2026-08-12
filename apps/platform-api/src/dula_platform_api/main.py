"""Platform API application factory (docs/05-Backend/APIArchitecture.md)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dula_common.events import EventPublisher
from dula_common.logging import configure_logging
from dula_common.opa import OPAClient
from dula_common.telemetry import setup_telemetry
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dula_platform_api.config import Settings, get_settings
from dula_platform_api.db import make_engine, make_sessionmaker
from dula_platform_api.routers import alerts, assets, health, incidents, me


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = app.state.settings
    engine = make_engine(settings.database_url)
    app.state.engine = engine
    app.state.sessionmaker = make_sessionmaker(engine)
    app.state.opa = OPAClient(settings.opa_url)
    publisher = EventPublisher(
        settings.kafka_bootstrap_servers,
        topic=settings.events_topic,
        enabled=settings.events_enabled,
    )
    await publisher.start()
    app.state.publisher = publisher
    try:
        yield
    finally:
        await publisher.stop()
        await engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    setup_telemetry(settings.service_name)

    app = FastAPI(title="Dula Platform API", version="0.2.0", lifespan=lifespan)
    app.state.settings = settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(me.router)
    app.include_router(assets.router)
    app.include_router(incidents.router)
    app.include_router(alerts.router)
    return app


app = create_app()
