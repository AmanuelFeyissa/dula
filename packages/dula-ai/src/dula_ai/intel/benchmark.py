"""Domain benchmark suites for cyber-intelligence (docs/08-AI/Benchmarking.md).

Fixed, labelled cases that grade the deterministic intel capabilities so quality cannot regress
silently ("evaluation gates everything"): CTI extraction (IOC/TTP precision & recall) and
detection authoring (syntactic validity of generated rules). Offline and reproducible — used by
CI tests and re-usable by the evaluation harness.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from dula_ai.intel.attack import extract_techniques
from dula_ai.intel.iocs import extract


@dataclass(frozen=True, slots=True)
class CTICase:
    advisory: str
    expected_iocs: frozenset[str]  # normalised "kind:value" pairs
    expected_techniques: frozenset[str]  # technique IDs


# Curated CTI extraction cases — defanged indicators and mixed prose (the realistic shape of
# advisories). Labels are the indicators/techniques a competent analyst would extract.
CTI_BENCHMARK: tuple[CTICase, ...] = (
    CTICase(
        advisory=(
            "The actor sent spearphishing emails with a malicious link to "
            "hxxp://bad[.]example[.]com. The dropper contacted 198.51.100.23 and used "
            "PowerShell for execution. See CVE-2023-1111."
        ),
        expected_iocs=frozenset(
            {"url:http://bad.example.com", "ipv4:198.51.100.23", "cve:CVE-2023-1111"}
        ),
        expected_techniques=frozenset({"T1566", "T1059"}),
    ),
    CTICase(
        advisory=(
            "Ransomware encrypted files and dropped a ransom note. C2 domain evil[.]net "
            "resolved to 203.0.113.9. Payload SHA-256 " + "b" * 64 + "."
        ),
        expected_iocs=frozenset({"domain:evil.net", "ipv4:203.0.113.9", "sha256:" + "b" * 64}),
        expected_techniques=frozenset({"T1486"}),
    ),
    CTICase(
        advisory=(
            "Adversaries performed credential dumping from LSASS using mimikatz, then moved "
            "laterally via RDP. Exfiltration used hxxps://drop[.]site[.]org/upload."
        ),
        expected_iocs=frozenset({"url:https://drop.site.org/upload"}),
        expected_techniques=frozenset({"T1003", "T1021"}),
    ),
)


@dataclass(frozen=True, slots=True)
class PRF:
    precision: float
    recall: float
    f1: float


def _prf(predicted: set[str], expected: set[str]) -> PRF:
    if not expected:
        return PRF(1.0, 1.0, 1.0)
    tp = len(predicted & expected)
    precision = tp / len(predicted) if predicted else 0.0
    recall = tp / len(expected)
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return PRF(round(precision, 3), round(recall, 3), round(f1, 3))


@dataclass(frozen=True, slots=True)
class ExtractionScore:
    ioc: PRF
    technique: PRF


def score_cti() -> ExtractionScore:
    """Score IOC + technique extraction across the CTI benchmark (micro-averaged)."""
    ioc_pred: set[str] = set()
    ioc_exp: set[str] = set()
    tech_pred: set[str] = set()
    tech_exp: set[str] = set()
    for i, case in enumerate(CTI_BENCHMARK):
        for ind in extract(case.advisory):
            ioc_pred.add(f"{i}|{ind.kind}:{ind.value}")
        for e in case.expected_iocs:
            ioc_exp.add(f"{i}|{e}")
        for t in extract_techniques(case.advisory):
            tech_pred.add(f"{i}|{t.id}")
        for e in case.expected_techniques:
            tech_exp.add(f"{i}|{e}")
    return ExtractionScore(ioc=_prf(ioc_pred, ioc_exp), technique=_prf(tech_pred, tech_exp))


@dataclass(frozen=True, slots=True)
class DetectionCase:
    title: str
    advisory: str
    attack_tags: list[str] = field(default_factory=list)


# Authoring cases — each must yield a syntactically valid Sigma and YARA rule.
DETECTION_BENCHMARK: tuple[DetectionCase, ...] = (
    DetectionCase(
        title="Suspicious C2 domain beacon",
        advisory="Malware beacons to evil[.]example[.]com and 198.51.100.23 over HTTP.",
        attack_tags=["attack.t1071"],
    ),
    DetectionCase(
        title="Phishing payload delivery URL",
        advisory="User clicked hxxps://phish[.]bad[.]org/login harvesting credentials.",
        attack_tags=["attack.t1566"],
    ),
)
