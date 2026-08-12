"""Platform API configuration (12-factor; secrets from env/Vault, never hardcoded)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    service_name: str = "platform-api"
    log_level: str = "INFO"

    # Postgres (async driver). Local dev default matches docker-compose.dev.yml.
    database_url: str = "postgresql+asyncpg://dula:dula_dev_password@localhost:5432/dula"

    # Keycloak / OIDC (ADR-0009).
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "dula"
    api_audience: str = "dula-api"

    # CORS: the web app origin.
    cors_origins: list[str] = ["http://localhost:3000"]

    @property
    def issuer(self) -> str:
        return f"{self.keycloak_url.rstrip('/')}/realms/{self.keycloak_realm}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
