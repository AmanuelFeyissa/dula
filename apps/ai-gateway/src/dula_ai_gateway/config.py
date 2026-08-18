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

    # Canary rollout (Phase 10/M011, docs/09-MLOps/DeploymentPipelines.md #2). Unset (default)
    # = no canary: the gateway serves `provider` only, exactly as before. Set both
    # canary_candidate_model and canary_candidate_base_url to wire a candidate in; the
    # candidate receives no traffic until canary_weight is raised above 0 -- so a candidate
    # serving pool can be deployed and its wiring verified before it takes real requests.
    canary_candidate_model: str = ""
    canary_candidate_base_url: str = ""
    canary_candidate_api_key: str = ""
    canary_weight: float = 0.0

    embedding_dim: int = 256
    top_k: int = 5
    max_tokens_per_tenant: int = 200_000

    # Seed the built-in demo public corpus at startup so answers are grounded out of the box.
    seed_demo_corpus: bool = True

    # Plugin/connector egress (Phase 07). Off by default = air-gapped: connectors that require
    # network egress (e.g. live TI feeds) are inert until this is enabled with an allowlist.
    plugins_egress_enabled: bool = False

    # Event backbone (ADR-0004) for AI-call audit events.
    events_enabled: bool = True
    kafka_bootstrap_servers: str = "localhost:19092"
    events_topic: str = "dula.domain.events"

    # Agent/playbook run persistence (ADR-0016). "memory" is the offline/air-gapped default —
    # no Postgres required to run the gateway at all; "postgres" makes runs (and their
    # approvals) survive a restart. Same default database as platform-api, different tables.
    run_store: Literal["memory", "postgres"] = "memory"
    database_url: str = "postgresql+asyncpg://dula:dula_dev_password@localhost:5432/dula"

    @property
    def issuer(self) -> str:
        return f"{self.keycloak_url.rstrip('/')}/realms/{self.keycloak_realm}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
