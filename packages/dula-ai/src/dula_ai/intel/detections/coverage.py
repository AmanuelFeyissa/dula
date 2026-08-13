"""ATT&CK coverage mapping for detection sets (UC-04).

Given the ATT&CK tags carried by a set of detection rules, report which techniques and tactics
are covered and — against an optional target technique set — which remain gaps. Sigma-style
tags (``attack.t1059``, ``attack.t1059.001``) and bare technique IDs are both accepted. Pure,
offline, catalog-backed (docs/08-AI/Benchmarking.md).
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

from dula_ai.intel.attack import Technique, lookup

_TAG_RE = re.compile(r"(?:attack\.)?(t\d{4}(?:\.\d{3})?)", re.I)


def technique_ids_from_tags(tags: Iterable[str]) -> list[str]:
    """Extract normalised ATT&CK technique IDs from Sigma-style or bare tags."""
    ids: list[str] = []
    for tag in tags:
        m = _TAG_RE.fullmatch(tag.strip()) or _TAG_RE.search(tag)
        if m:
            ids.append(m.group(1).upper())
    return ids


@dataclass(frozen=True, slots=True)
class CoverageReport:
    covered_techniques: list[Technique]
    covered_tactics: list[str]
    gaps: list[str] = field(default_factory=list)  # target technique IDs with no rule
    coverage_ratio: float = 0.0  # fraction of the target set covered (0-1)


def coverage(
    rule_tag_sets: Sequence[Iterable[str]],
    *,
    target: Iterable[str] | None = None,
) -> CoverageReport:
    """Summarise ATT&CK coverage across a set of rules.

    ``rule_tag_sets`` is one tag list per rule. ``target`` is an optional set of technique IDs
    the detection library aims to cover; gaps and a coverage ratio are computed against it.
    """
    covered: dict[str, Technique] = {}
    for tags in rule_tag_sets:
        for tid in technique_ids_from_tags(tags):
            tech = lookup(tid)
            if tech is not None:
                covered[tid.upper()] = tech
            else:
                covered[tid.upper()] = Technique(tid.upper(), "Unknown", "unknown")

    tactics = sorted({t.tactic for t in covered.values() if t.tactic != "unknown"})
    techniques = sorted(covered.values(), key=lambda t: t.id)

    gaps: list[str] = []
    ratio = 0.0
    if target is not None:
        target_ids = {t.upper() for t in target}
        # A parent technique (T1059) counts as covering its sub-technique targets and vice-versa.
        covered_parents = {tid.split(".", 1)[0] for tid in covered}
        hit = {t for t in target_ids if t in covered or t.split(".", 1)[0] in covered_parents}
        gaps = sorted(target_ids - hit)
        ratio = round(len(hit) / len(target_ids), 3) if target_ids else 0.0

    return CoverageReport(
        covered_techniques=techniques,
        covered_tactics=tactics,
        gaps=gaps,
        coverage_ratio=ratio,
    )
