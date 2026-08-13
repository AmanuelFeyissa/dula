"""Plugin manifest + capability model (docs/14-Plugins/PluginFramework.md §1).

A manifest is the plugin's declared, signed contract: its identity, version, publisher key,
the capabilities it offers (each with a side-effect class and the permission it requires), the
external hosts it needs to reach (egress allowlist), and its resource limits. The host grants
**only** what the manifest declares (least privilege) and enforces egress against exactly the
declared hosts. Canonical JSON (`canonical_bytes`) is what gets signed/verified, so any tampering
with the manifest invalidates the signature.
"""

from __future__ import annotations

import json
from enum import StrEnum

from pydantic import BaseModel, Field

_ID_PATTERN = r"^dula-plugin-[a-z0-9]+(-[a-z0-9]+)+$"
_CAP_PATTERN = r"^[a-z0-9]+\.[a-z0-9_]+$"
_HOST_PATTERN = r"^[a-z0-9.-]+$"


class SideEffect(StrEnum):
    READ = "read"
    CONSEQUENTIAL = "consequential"


class Capability(BaseModel):
    """One connector capability, named ``<system>.<capability>`` (ConnectorStandards.md §1)."""

    name: str = Field(pattern=_CAP_PATTERN, max_length=64)
    side_effect: SideEffect
    permission: str = Field(min_length=1, max_length=64)  # OPA action gating this capability
    description: str = Field(default="", max_length=256)
    requires_egress: bool = False  # if true, the capability needs network egress to function


class ResourceLimits(BaseModel):
    timeout_seconds: float = Field(default=10.0, gt=0, le=120)
    max_output_bytes: int = Field(default=1_000_000, gt=0, le=50_000_000)


class PluginManifest(BaseModel):
    """The signed contract for a plugin (identity + capabilities + egress + limits)."""

    id: str = Field(pattern=_ID_PATTERN, max_length=128)
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    publisher_key_id: str = Field(min_length=1, max_length=128)
    description: str = Field(default="", max_length=512)
    capabilities: list[Capability] = Field(min_length=1)
    egress: list[str] = Field(default_factory=list)  # allowlisted external hostnames
    limits: ResourceLimits = Field(default_factory=ResourceLimits)

    def capability(self, name: str) -> Capability | None:
        return next((c for c in self.capabilities if c.name == name), None)

    def canonical_bytes(self) -> bytes:
        """Deterministic serialization for signing/verification (sorted keys, no whitespace)."""
        return json.dumps(
            self.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
