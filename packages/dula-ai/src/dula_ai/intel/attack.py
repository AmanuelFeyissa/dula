"""MITRE ATT&CK technique reference + TTP extraction (UC-05).

A small, embedded ATT&CK catalog (offline — no live STIX download) sufficient for extracting
technique references from advisory text and mapping detections to coverage. Two extraction
paths: explicit technique IDs (``T1059``, ``T1059.001``) via regex, and keyword association for
techniques named only in prose. The catalog is intentionally curated (not exhaustive); the full
ATT&CK dataset is ingested via the knowledge pipeline (FUTURE, DatasetStrategy.md).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

_TECHNIQUE_ID = re.compile(r"\bT\d{4}(?:\.\d{3})?\b")


@dataclass(frozen=True, slots=True)
class Technique:
    id: str
    name: str
    tactic: str
    keywords: tuple[str, ...] = field(default_factory=tuple)


# Curated subset of ATT&CK Enterprise, chosen to cover the most common CTI narrative phrases.
# Rows are (id, name, tactic, keywords); ruff-format wraps the keyword tuples to fit the width.
_ROWS: tuple[tuple[str, str, str, tuple[str, ...]], ...] = (
    (
        "T1566",
        "Phishing",
        "initial-access",
        ("phishing", "spearphishing", "malicious attachment", "malicious link"),
    ),
    (
        "T1190",
        "Exploit Public-Facing Application",
        "initial-access",
        ("exploit public-facing", "web shell upload", "vulnerable application", "internet-facing"),
    ),
    (
        "T1078",
        "Valid Accounts",
        "defense-evasion",
        ("valid account", "compromised credential", "stolen credential"),
    ),
    (
        "T1059",
        "Command and Scripting Interpreter",
        "execution",
        ("powershell", "command interpreter", "cmd.exe", "bash script", "wscript"),
    ),
    ("T1059.001", "PowerShell", "execution", ("powershell", "encoded command", "-enc ")),
    ("T1053", "Scheduled Task/Job", "persistence", ("scheduled task", "cron job", "schtasks")),
    (
        "T1547",
        "Boot or Logon Autostart Execution",
        "persistence",
        ("registry run key", "startup folder", "autostart"),
    ),
    (
        "T1055",
        "Process Injection",
        "defense-evasion",
        ("process injection", "reflective loading", "dll injection"),
    ),
    (
        "T1027",
        "Obfuscated Files or Information",
        "defense-evasion",
        ("obfuscated", "base64 encoded", "packed", "encoded payload"),
    ),
    (
        "T1003",
        "OS Credential Dumping",
        "credential-access",
        ("credential dumping", "lsass", "mimikatz", "sam database"),
    ),
    (
        "T1110",
        "Brute Force",
        "credential-access",
        ("brute force", "password spraying", "credential stuffing", "password guessing"),
    ),
    (
        "T1021",
        "Remote Services",
        "lateral-movement",
        ("remote desktop", "rdp", "psexec", "winrm", "smb"),
    ),
    (
        "T1071",
        "Application Layer Protocol",
        "command-and-control",
        ("command and control", "c2 channel", "http beacon", "dns tunneling"),
    ),
    (
        "T1105",
        "Ingress Tool Transfer",
        "command-and-control",
        ("download additional", "ingress tool", "payload download", "second-stage"),
    ),
    (
        "T1486",
        "Data Encrypted for Impact",
        "impact",
        ("ransomware", "encrypt files", "ransom note", "data encrypted for impact"),
    ),
    (
        "T1567",
        "Exfiltration Over Web Service",
        "exfiltration",
        ("exfiltrate", "data exfiltration", "upload to"),
    ),
    (
        "T1041",
        "Exfiltration Over C2 Channel",
        "exfiltration",
        ("exfiltration over c2", "exfiltrate over command"),
    ),
)

CATALOG: tuple[Technique, ...] = tuple(Technique(*row) for row in _ROWS)

_BY_ID: dict[str, Technique] = {t.id: t for t in CATALOG}


def lookup(technique_id: str) -> Technique | None:
    """Return the catalog entry for a technique ID, falling back to its parent technique."""
    tid = technique_id.upper()
    if tid in _BY_ID:
        return _BY_ID[tid]
    parent = tid.split(".", 1)[0]
    return _BY_ID.get(parent)


def extract_techniques(text: str) -> list[Technique]:
    """Extract ATT&CK techniques referenced by explicit ID or by keyword, ordered by ID."""
    hits: dict[str, Technique] = {}
    for raw in _TECHNIQUE_ID.findall(text):
        tech = lookup(raw)
        if tech is not None:
            hits[tech.id] = tech
    lowered = text.lower()
    for tech in CATALOG:
        if tech.id in hits:
            continue
        if any(kw in lowered for kw in tech.keywords):
            hits[tech.id] = tech
    return sorted(hits.values(), key=lambda t: t.id)
