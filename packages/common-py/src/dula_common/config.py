"""Base configuration primitives shared across Dula services.

Services subclass these with their own settings. Config comes from the environment
(12-factor); never hardcode secrets (docs/10-Security/DataSecurity.md).
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class CommonSettings(BaseSettings):
    """Settings common to every Dula service."""

    model_config = SettingsConfigDict(env_prefix="DULA_", extra="ignore")

    env: str = "dev"
    log_level: str = "INFO"
    service_name: str = "dula-service"
