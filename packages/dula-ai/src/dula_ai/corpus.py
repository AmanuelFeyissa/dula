"""A tiny built-in public-knowledge corpus for offline demo and evaluation.

These are short, illustrative paraphrases of well-known public security knowledge
(MITRE ATT&CK techniques, common CVE-class issues, CISA guidance) — not full feeds. They let
RAG, the demo, and the evaluation benchmark run fully offline. Real ingestion of upstream
feeds is handled by the knowledge pipeline (FUTURE), governed by DatasetStrategy.md.
"""

from __future__ import annotations

from dula_ai.knowledge import Document

DEMO_PUBLIC_CORPUS: list[Document] = [
    Document(
        id="attack-t1110",
        source="mitre-attack",
        license="MITRE-ATT&CK",
        text=(
            "Brute Force (T1110): Adversaries may use brute force techniques to gain access to "
            "accounts when passwords are unknown or when password hashes are obtained. Common "
            "forms include password guessing, password spraying, and credential stuffing. "
            "Mitigations include account lockout policies, multi-factor authentication, and "
            "monitoring for many failed authentication attempts from a single source."
        ),
    ),
    Document(
        id="attack-t1566",
        source="mitre-attack",
        license="MITRE-ATT&CK",
        text=(
            "Phishing (T1566): Adversaries send phishing messages to gain access to victim "
            "systems, often via malicious attachments or links. Spearphishing targets specific "
            "individuals. Detection relies on email security controls, user reporting, and "
            "analysis of anomalous links and attachments."
        ),
    ),
    Document(
        id="attack-t1059",
        source="mitre-attack",
        license="MITRE-ATT&CK",
        text=(
            "Command and Scripting Interpreter (T1059): Adversaries abuse command interpreters "
            "such as PowerShell, Bash, and cmd to execute commands and scripts. PowerShell "
            "(T1059.001) is frequently used for post-exploitation. Enable script-block logging "
            "and monitor for suspicious interpreter usage."
        ),
    ),
    Document(
        id="cve-log4shell",
        source="nvd-cve",
        license="public-domain",
        text=(
            "Log4Shell (CVE-2021-44228) is a critical remote code execution vulnerability in "
            "Apache Log4j 2 via JNDI lookups in logged strings. An attacker who can cause a "
            "crafted string to be logged can execute arbitrary code. Remediation is to upgrade "
            "Log4j and disable JNDI lookups."
        ),
    ),
    Document(
        id="cve-eternalblue",
        source="nvd-cve",
        license="public-domain",
        text=(
            "EternalBlue (CVE-2017-0144) is a vulnerability in Microsoft SMBv1 allowing remote "
            "code execution. It was used by WannaCry and NotPetya. Mitigation includes applying "
            "MS17-010 patches and disabling SMBv1."
        ),
    ),
    Document(
        id="cisa-mfa",
        source="cisa-kev",
        license="public-domain",
        text=(
            "CISA recommends phishing-resistant multi-factor authentication (MFA) to defend "
            "against credential theft and account takeover. FIDO2/WebAuthn hardware keys provide "
            "the strongest protection against phishing of authentication."
        ),
    ),
]
