"""YARA rule authoring + validation (UC-04).

A structured YARA model, a deterministic emitter, and a dependency-free validator that enforces
the grammar a YARA engine requires: a valid rule identifier, balanced braces, a ``condition``,
and every string identifier used in the condition being defined in ``strings``. Rules are
authored from indicators and always validated before return, so generated YARA is syntactically
valid and reviewable. File hashes are recorded in ``meta`` for provenance (a hash is not a
content string to scan for); network/host indicators become text strings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from dula_ai.intel.iocs import Indicator

_RULE_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_STRING_REF_RE = re.compile(r"\$[A-Za-z0-9_]+|\$\*")
_YARA_KEYWORDS = frozenset(
    {
        "rule",
        "meta",
        "strings",
        "condition",
        "and",
        "or",
        "not",
        "all",
        "any",
        "of",
        "them",
        "for",
        "in",
        "at",
        "filesize",
        "entrypoint",
        "true",
        "false",
        "import",
        "include",
        "global",
        "private",
    }
)
# IOC kinds that are meaningful as scannable content strings (vs. hashes → meta provenance).
_STRING_KINDS = frozenset({"domain", "url", "ipv4", "ipv6", "email"})
_HASH_KINDS = frozenset({"md5", "sha1", "sha256"})


@dataclass(frozen=True, slots=True)
class YaraString:
    identifier: str  # includes leading '$'
    value: str
    modifiers: tuple[str, ...] = ()  # e.g. ("ascii", "wide", "nocase")


@dataclass(frozen=True, slots=True)
class YaraRule:
    name: str
    strings: list[YaraString]
    condition: str
    meta: dict[str, str] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ValidationResult:
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def render(rule: YaraRule) -> str:
    """Emit a deterministic, well-formed YARA rule."""
    header = f"rule {rule.name}"
    if rule.tags:
        header += " : " + " ".join(rule.tags)
    lines = [header, "{"]
    if rule.meta:
        lines.append("    meta:")
        lines.extend(f'        {k} = "{_escape(v)}"' for k, v in rule.meta.items())
    if rule.strings:
        lines.append("    strings:")
        for s in rule.strings:
            mods = (" " + " ".join(s.modifiers)) if s.modifiers else ""
            lines.append(f'        {s.identifier} = "{_escape(s.value)}"{mods}')
    lines.append("    condition:")
    lines.append(f"        {rule.condition}")
    lines.append("}")
    return "\n".join(lines) + "\n"


def validate(rule: YaraRule) -> ValidationResult:
    """Structurally validate a YARA rule model."""
    errors: list[str] = []
    warnings: list[str] = []

    if not _RULE_NAME_RE.match(rule.name):
        errors.append(f"invalid rule name: {rule.name!r}")
    elif rule.name in _YARA_KEYWORDS:
        errors.append(f"rule name is a reserved keyword: {rule.name}")

    defined = {s.identifier for s in rule.strings}
    for s in rule.strings:
        if not s.identifier.startswith("$"):
            errors.append(f"string identifier must start with '$': {s.identifier}")
        if not s.value:
            errors.append(f"string {s.identifier} is empty")

    condition = rule.condition.strip()
    if not condition:
        errors.append("condition is empty")
    else:
        refs = set(_STRING_REF_RE.findall(condition))
        wildcard = any(r.endswith("*") for r in refs) or "them" in condition.split()
        concrete = {r for r in refs if not r.endswith("*")}
        undefined = sorted(r for r in concrete if r not in defined)
        if undefined:
            errors.append(f"condition references undefined string(s): {', '.join(undefined)}")
        if not defined and wildcard:
            errors.append("condition uses 'them'/wildcard but no strings are defined")

    if not rule.strings and "them" in condition:
        warnings.append("no strings defined; condition may never match")
    return ValidationResult(valid=not errors, errors=errors, warnings=warnings)


def validate_text(text: str) -> ValidationResult:
    """Lightweight structural check for an externally-supplied YARA rule (dependency-free)."""
    errors: list[str] = []
    if not re.search(r"(?m)^\s*rule\s+[A-Za-z_][A-Za-z0-9_]*", text):
        errors.append("missing 'rule <name>' declaration")
    if text.count("{") != text.count("}"):
        errors.append("unbalanced braces")
    if not re.search(r"(?m)^\s*condition\s*:", text):
        errors.append("missing 'condition:' block")
    return ValidationResult(valid=not errors, errors=errors)


def build_ioc_rule(
    *,
    name: str,
    indicators: list[Indicator],
    meta: dict[str, str] | None = None,
    tags: list[str] | None = None,
) -> tuple[YaraRule, str, ValidationResult]:
    """Deterministically author a YARA rule from indicators.

    Host/network indicators become ``ascii wide`` content strings; file hashes are recorded in
    ``meta`` as provenance. Returns the model, rendered rule, and (valid) validation result.
    """
    strings: list[YaraString] = []
    rule_meta = dict(meta or {})
    idx = 0
    for ind in indicators:
        if ind.kind in _STRING_KINDS:
            strings.append(YaraString(f"$s{idx}", ind.value, ("ascii", "wide", "nocase")))
            idx += 1
        elif ind.kind in _HASH_KINDS:
            rule_meta.setdefault(ind.kind, ind.value)
    if not strings:
        raise ValueError("no content indicators to build YARA strings from")

    condition = "any of them"
    rule = YaraRule(
        name=name,
        strings=strings,
        condition=condition,
        meta={"author": "Dula", "description": f"Detects indicators for {name}", **rule_meta},
        tags=tags or [],
    )
    return rule, render(rule), validate(rule)
