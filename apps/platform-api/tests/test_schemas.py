"""Unit tests for domain schema validation (no DB)."""

from __future__ import annotations

import uuid

import pytest
from dula_platform_api.models import Criticality
from dula_platform_api.schemas import AlertCreate, AssetCreate, AssetUpdate
from pydantic import ValidationError


def test_asset_create_defaults() -> None:
    asset = AssetCreate(name="web-01")
    assert asset.asset_type == "other"
    assert asset.criticality == "medium"


def test_asset_create_rejects_bad_enum() -> None:
    with pytest.raises(ValidationError):
        AssetCreate(name="web-01", criticality="catastrophic")  # type: ignore[arg-type]


def test_asset_create_rejects_empty_name() -> None:
    with pytest.raises(ValidationError):
        AssetCreate(name="")


def test_asset_update_exclude_unset_is_partial() -> None:
    # Only the provided field appears — a PATCH must not overwrite others with defaults.
    update = AssetUpdate(criticality=Criticality.HIGH)
    assert update.model_dump(exclude_unset=True) == {"criticality": "high"}


def test_alert_create_accepts_optional_links() -> None:
    alert = AlertCreate(title="suspicious login", asset_id=uuid.uuid4())
    assert alert.severity == "medium"
    assert alert.status == "new"
