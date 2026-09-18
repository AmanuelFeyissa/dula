"""Unit tests for provider wiring, including the optional canary path (M011 PR B)."""

from __future__ import annotations

from dula_ai.metering import MeteredProvider
from dula_ai.providers import CanaryProvider, ExtractiveProvider
from dula_ai_gateway.config import Settings
from dula_ai_gateway.wiring import _provider


def test_provider_defaults_to_extractive_with_no_canary_configured() -> None:
    settings = Settings(profile="offline")
    provider = _provider(settings)
    # Always metered under the "production" role; no canary wrapper without a candidate.
    assert isinstance(provider, MeteredProvider) and not isinstance(provider, CanaryProvider)
    assert isinstance(provider._inner, ExtractiveProvider)
    assert provider.name == ExtractiveProvider().name


def test_provider_stays_unwrapped_when_only_one_canary_field_is_set() -> None:
    settings = Settings(profile="offline", canary_candidate_model="dula-ai-v2")
    provider = _provider(settings)
    assert isinstance(provider, MeteredProvider) and not isinstance(provider, CanaryProvider)
    assert isinstance(provider._inner, ExtractiveProvider)


def test_provider_wraps_in_canary_when_both_candidate_fields_are_set() -> None:
    settings = Settings(
        profile="offline",
        canary_candidate_model="dula-ai-v2",
        canary_candidate_base_url="http://candidate:8000/v1",
        canary_weight=0.25,
    )
    provider = _provider(settings)
    assert isinstance(provider, CanaryProvider)
    assert "dula-ai-v2" in provider.name
