"""Worker configuration (12-factor; secrets from env/Vault)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    service_name: str = "worker"
    log_level: str = "INFO"

    kafka_bootstrap_servers: str = "localhost:19092"
    events_topic: str = "dula.domain.events"
    consumer_group: str = "dula-worker"


@lru_cache
def get_settings() -> Settings:
    return Settings()
