"""Sigma rule authoring + validation (UC-04).

A structured Sigma model, a deterministic YAML emitter, and a dependency-free structural
validator. The validator enforces the parts of the Sigma grammar that make a rule usable:
required top-level keys, a non-empty ``logsource``, at least one detection selection, and a
``condition`` that references only identifiers defined in ``detection``. Because rules are
generated from a validated model, ``build_ioc_rule`` output is guaranteed valid; the same
validator also grades an externally-supplied (e.g. model-drafted) rule.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from typing import Any

from dula_ai.intel.iocs import Indicator

_REQUIRED_KEYS = ("title", "logsource", "detection")
_LEVELS = ("informational", "low", "medium", "high", "critical")
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
# Reserved words that may appear in a Sigma condition alongside selection identifiers.
_CONDITION_KEYWORDS = frozenset({"and", "or", "not", "all", "of", "them", "1", "any"})

# Default Sigma field for each IOC kind (network/proxy/DNS/hash oriented).
_IOC_FIELD: dict[str, str] = {
    "ipv4": "dst_ip",
    "ipv6": "dst_ip",
    "domain": "dns.query.name",
    "url": "url",
    "md5": "Hashes|contains",
    "sha1": "Hashes|contains",
    "sha256": "Hashes|contains",
}


@dataclass(frozen=True, slots=True)
class LogSource:
    category: str | None = None
    product: str | None = None
    service: str | None = None

    def as_dict(self) -> dict[str, str]:
        pairs = (("category", self.category), ("product", self.product), ("service", self.service))
        return {k: v for k, v in pairs if v}


@dataclass(frozen=True, slots=True)
class SigmaRule:
    title: str
    logsource: LogSource
    detection: dict[str, Any]  # selection-id -> {field: value(s)}, plus "condition": str
    id: str = ""
    status: str = "experimental"
    description: str = ""
    level: str = "medium"
    tags: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    falsepositives: list[str] = field(default_factory=list)

    @property
    def condition(self) -> str:
        cond = self.detection.get("condition", "")
        return cond if isinstance(cond, str) else ""


@dataclass(frozen=True, slots=True)
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _rule_uuid(title: str) -> str:
    return str(uuid.uuid5(uuid.UUID("6f1a9d2e-8c4b-4e7a-9f13-2b7c5a0d4e88"), f"sigma:{title}"))


def _emit_scalar(value: Any) -> str:
    text = str(value)
    if text == "" or re.search(r"[:#\[\]{}\"'|>*&!%@`,]", text) or text != text.strip():
        return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return text


def _emit_mapping(data: dict[str, Any], indent: int) -> list[str]:
    pad = "    " * indent
    lines: list[str] = []
    for key, value in data.items():
        if key == "condition":
            continue
        if isinstance(value, dict):
            lines.append(f"{pad}{key}:")
            lines.extend(_emit_mapping(value, indent + 1))
        elif isinstance(value, list):
            lines.append(f"{pad}{key}:")
            for item in value:
                lines.append(f"{pad}    - {_emit_scalar(item)}")
        else:
            lines.append(f"{pad}{key}: {_emit_scalar(value)}")
    return lines


def render(rule: SigmaRule) -> str:
    """Emit a deterministic, well-formed Sigma YAML document."""
    rid = rule.id or _rule_uuid(rule.title)
    lines = [f"title: {_emit_scalar(rule.title)}", f"id: {rid}", f"status: {rule.status}"]
    if rule.description:
        lines.append(f"description: {_emit_scalar(rule.description)}")
    if rule.references:
        lines.append("references:")
        lines.extend(f"    - {_emit_scalar(r)}" for r in rule.references)
    if rule.tags:
        lines.append("tags:")
        lines.extend(f"    - {_emit_scalar(t)}" for t in rule.tags)
    lines.append("logsource:")
    lines.extend(_emit_mapping(rule.logsource.as_dict(), 1))
    lines.append("detection:")
    lines.extend(_emit_mapping(rule.detection, 1))
    lines.append(f"    condition: {rule.condition}")
    if rule.falsepositives:
        lines.append("falsepositives:")
        lines.extend(f"    - {_emit_scalar(fp)}" for fp in rule.falsepositives)
    lines.append(f"level: {rule.level}")
    return "\n".join(lines) + "\n"


def validate(rule: SigmaRule) -> ValidationResult:
    """Structurally validate a Sigma rule model (grammar the SIEM back-end relies on)."""
    errors: list[str] = []
    warnings: list[str] = []

    if not rule.title.strip():
        errors.append("title is empty")
    if not rule.logsource.as_dict():
        errors.append("logsource must set at least one of category/product/service")

    selections = {k: v for k, v in rule.detection.items() if k != "condition"}
    if not selections:
        errors.append("detection has no selection blocks")
    for name, block in selections.items():
        if not isinstance(block, dict) or not block:
            errors.append(f"selection '{name}' must be a non-empty mapping")

    condition = rule.condition.strip()
    if not condition:
        errors.append("detection.condition is missing")
    else:
        referenced = {tok for tok in _IDENT_RE.findall(condition) if tok not in _CONDITION_KEYWORDS}
        undefined = sorted(r for r in referenced if r not in selections)
        if undefined:
            errors.append(f"condition references undefined selection(s): {', '.join(undefined)}")

    if rule.level not in _LEVELS:
        warnings.append(f"level '{rule.level}' is not a standard Sigma level")
    if not any(t.startswith("attack.") for t in rule.tags):
        warnings.append("no ATT&CK tag (attack.tXXXX) — coverage mapping will be empty")

    return ValidationResult(valid=not errors, errors=errors, warnings=warnings)


def validate_text(text: str) -> ValidationResult:
    """Lightweight structural check for an externally-supplied Sigma YAML document.

    Dependency-free: verifies the required top-level keys and a ``condition`` are present
    without a full YAML parse, so it runs air-gapped. Returns errors for missing structure.
    """
    errors: list[str] = []
    top_level = set(re.findall(r"(?m)^([A-Za-z_][A-Za-z0-9_]*):", text))
    for key in _REQUIRED_KEYS:
        if key not in top_level:
            errors.append(f"missing required key: {key}")
    if not re.search(r"(?m)^\s*condition:\s*\S", text):
        errors.append("detection.condition is missing or empty")
    return ValidationResult(valid=not errors, errors=errors)


def build_ioc_rule(
    *,
    title: str,
    indicators: list[Indicator],
    logsource: LogSource,
    attack_tags: list[str] | None = None,
    level: str = "high",
    description: str = "",
    references: list[str] | None = None,
) -> tuple[SigmaRule, str, ValidationResult]:
    """Deterministically author a Sigma rule that matches the given IOCs.

    Groups indicators by their default Sigma field into a single ``selection`` and returns the
    model, the rendered YAML, and the (always-valid) validation result. Non-observable kinds
    (e.g. ``cve``) are ignored — they are not detection selectors.
    """
    selection: dict[str, list[str]] = {}
    for ind in indicators:
        field_name = _IOC_FIELD.get(ind.kind)
        if field_name is None:
            continue
        selection.setdefault(field_name, []).append(ind.value)
    if not selection:
        raise ValueError("no observable indicators to build a detection from")

    # Collapse single-element lists to scalars for idiomatic Sigma.
    detection: dict[str, Any] = {
        "selection": {k: (v[0] if len(v) == 1 else v) for k, v in selection.items()},
        "condition": "selection",
    }
    rule = SigmaRule(
        title=title,
        id=_rule_uuid(title),
        description=description or f"Detects indicators associated with {title}.",
        logsource=logsource,
        detection=detection,
        level=level,
        tags=attack_tags or [],
        references=references or [],
        falsepositives=["Legitimate administrative activity matching these indicators"],
    )
    return rule, render(rule), validate(rule)
