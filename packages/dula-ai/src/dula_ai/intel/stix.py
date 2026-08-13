"""STIX 2.1 mapping (UC-05 — docs/07-Database/DataModel.md).

Maps extracted indicators and ATT&CK techniques to a deterministic STIX 2.1 bundle:
``indicator`` SDOs (with STIX-patterning) and ``attack-pattern`` SDOs. IDs are derived with
``uuid5`` over the object's identifying value, so the same intel always produces the same
bundle (diffable, idempotent) without pulling in a STIX library. Timestamps are optional and
supplied by the caller to keep the mapping a pure function.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from typing import Any

from dula_ai.intel.attack import Technique
from dula_ai.intel.iocs import Indicator

# Deterministic namespace for Dula-generated STIX IDs (a fixed random UUID, per RFC 4122 §4.3).
_NS = uuid.UUID("6f1a9d2e-8c4b-4e7a-9f13-2b7c5a0d4e88")
_EPOCH = "2020-01-01T00:00:00.000Z"

# IOC kind -> STIX Cyber-observable pattern path.
_PATTERN: dict[str, str] = {
    "ipv4": "ipv4-addr:value",
    "ipv6": "ipv6-addr:value",
    "domain": "domain-name:value",
    "url": "url:value",
    "email": "email-addr:value",
    "md5": "file:hashes.'MD5'",
    "sha1": "file:hashes.'SHA-1'",
    "sha256": "file:hashes.'SHA-256'",
}


def _id(kind: str, value: str) -> str:
    return f"{kind}--{uuid.uuid5(_NS, f'{kind}:{value}')}"


def _pattern(ind: Indicator) -> str | None:
    path = _PATTERN.get(ind.kind)
    if path is None:
        return None
    escaped = ind.value.replace("\\", "\\\\").replace("'", "\\'")
    return f"[{path} = '{escaped}']"


def indicator_sdo(ind: Indicator, *, created: str = _EPOCH) -> dict[str, Any] | None:
    """Build a STIX ``indicator`` SDO for an observable IOC (None for non-observable kinds)."""
    pattern = _pattern(ind)
    if pattern is None:
        return None
    return {
        "type": "indicator",
        "spec_version": "2.1",
        "id": _id("indicator", f"{ind.kind}:{ind.value}"),
        "created": created,
        "modified": created,
        "name": f"{ind.kind}: {ind.defanged}",
        "pattern": pattern,
        "pattern_type": "stix",
        "valid_from": created,
        "labels": ["malicious-activity"],
    }


def attack_pattern_sdo(tech: Technique, *, created: str = _EPOCH) -> dict[str, Any]:
    """Build a STIX ``attack-pattern`` SDO referencing an ATT&CK technique."""
    return {
        "type": "attack-pattern",
        "spec_version": "2.1",
        "id": _id("attack-pattern", tech.id),
        "created": created,
        "modified": created,
        "name": tech.name,
        "external_references": [{"source_name": "mitre-attack", "external_id": tech.id}],
        "x_mitre_tactic": tech.tactic,
    }


def build_bundle(
    indicators: Sequence[Indicator],
    techniques: Sequence[Technique],
    *,
    created: str = _EPOCH,
) -> dict[str, Any]:
    """Assemble a STIX 2.1 bundle from extracted indicators and techniques."""
    objects: list[dict[str, Any]] = []
    for ind in indicators:
        sdo = indicator_sdo(ind, created=created)
        if sdo is not None:
            objects.append(sdo)
    objects.extend(attack_pattern_sdo(t, created=created) for t in techniques)
    return {
        "type": "bundle",
        "id": f"bundle--{uuid.uuid5(_NS, ''.join(o['id'] for o in objects))}",
        "objects": objects,
    }
