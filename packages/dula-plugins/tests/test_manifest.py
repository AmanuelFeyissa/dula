"""Tests for manifest validation."""

from __future__ import annotations

import pytest
from dula_plugins.manifest import Capability, PluginManifest, SideEffect
from pydantic import ValidationError


def _cap() -> Capability:
    return Capability(
        name="siem.search", side_effect=SideEffect.READ, permission="connector.siem.search"
    )


def test_valid_manifest() -> None:
    m = PluginManifest(
        id="dula-plugin-acme-siem", version="1.0.0", publisher_key_id="acme", capabilities=[_cap()]
    )
    assert m.capability("siem.search") is not None
    assert m.capability("nope") is None


def test_bad_id_rejected() -> None:
    with pytest.raises(ValidationError):
        PluginManifest(id="acme-siem", version="1.0.0", publisher_key_id="a", capabilities=[_cap()])


def test_bad_capability_name_rejected() -> None:
    with pytest.raises(ValidationError):
        Capability(name="SiemSearch", side_effect=SideEffect.READ, permission="p")


def test_requires_at_least_one_capability() -> None:
    with pytest.raises(ValidationError):
        PluginManifest(id="dula-plugin-a-b", version="1.0.0", publisher_key_id="a", capabilities=[])
