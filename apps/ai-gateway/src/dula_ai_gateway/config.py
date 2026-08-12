"""AI Gateway configuration (12-factor; secrets from env/Vault)."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    service_name: str = "ai-gateway"
    log_level: str = "INFO"

    # Keycloak / OIDC (ADR-0009).
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "dula"
    api_audience: str = "dula-api"

    # Authorization (OPA, ADR-0009).
    opa_url: str = "http://localhost:8181"

    cors_origins: list[str] = ["http://localhost:3000"]

    # Deployment profile: "offline" = in-memory stores (air-gapped default);
    # "backed" = Qdrant + OpenSearch.
    profile: Literal["offline", "backed"] = "offline"

    # RAG stores (backed profile) — ADR-0003.
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "dula_knowledge"
    opensearch_url: str = "http://localhost:9200"
    opensearch_index: str = "dula-knowledge"

    # Model provider (ADR-0005). "extractive" is the offline default; "ollama" uses a local
    # server; "openai" uses any OpenAI-compatible endpoint (vLLM / llama.cpp) — this is how a
    # shipped Dula AI checkpoint (Phase 04) is served behind the gateway.
    provider: Literal["extractive", "ollama", "openai"] = "extractive"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_embed_model: str = "nomic-embed-text"
    # OpenAI-compatible serving (Dula AI / vLLM / llama.cpp).
    openai_base_url: str = "http://localhost:8000/v1"
    openai_model: str = "dula-ai"
    openai_api_key: str = ""

    embedding_dim: int = 256
    top_k: int = 5
    max_tokens_per_tenant: int = 200_000

    # Seed the built-in demo public corpus at startup so answers are grounded out of the box.
    seed_demo_corpus: bool = True

    # Event backbone (ADR-0004) for AI-call audit events.
    events_enabled: bool = True
    kafka_bootstrap_servers: str = "localhost:19092"
    events_topic: str = "dula.domain.events"

    @property
    def issuer(self) -> str:
        return f"{self.keycloak_url.rstrip('/')}/realms/{self.keycloak_realm}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
