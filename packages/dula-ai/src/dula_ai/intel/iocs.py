"""IOC extraction (UC-05 — docs/02-Vision/UseCases.md).

Deterministic indicator-of-compromise extraction from untrusted advisory text: IPv4/IPv6,
domains, URLs, emails, file hashes (MD5/SHA-1/SHA-256), and CVE IDs. Advisories routinely
**defang** indicators (``hxxp://``, ``1[.]2[.]3[.]4``, ``evil[.]com``, ``user[at]corp[.]com``)
so they are not accidentally clickable; we *refang* before matching and *defang* again on
output, so extracted intel is never emitted as a live, resolvable link (safe handling of
untrusted content).

Pure functions, no network — works air-gapped and is fully reproducible in CI.
"""

from __future__ import annotations

import ipaddress
import re
from collections.abc import Iterable
from dataclasses import dataclass

# IOC kinds we recognise, most-specific first (a SHA-256 must not be reported as an MD5, and a
# URL host must not also surface as a bare domain — see ``extract``).
IOCKind = str
KINDS: tuple[IOCKind, ...] = (
    "cve",
    "url",
    "email",
    "ipv4",
    "ipv6",
    "sha256",
    "sha1",
    "md5",
    "domain",
)


def _unhxxp(m: re.Match[str]) -> str:
    return "https" if "s" in m.group().lower() else "http"


# Refang: turn defanged advisory text back into real indicators before matching.
_REFANG = (
    (re.compile(r"h\s*[xX]{2}\s*ps?", re.I), _unhxxp),
    (re.compile(r"\[\s*\.\s*\]"), lambda _m: "."),
    (re.compile(r"\(\s*\.\s*\)"), lambda _m: "."),
    (re.compile(r"\{\s*\.\s*\}"), lambda _m: "."),
    (re.compile(r"\[\s*(?:at|@)\s*\]", re.I), lambda _m: "@"),
    (re.compile(r"\[\s*:\s*\]"), lambda _m: ":"),
    (re.compile(r"\s+dot\s+", re.I), lambda _m: "."),
)

_CVE = re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.I)
_URL = re.compile(r"\bhttps?://[^\s<>\"'\])]+", re.I)
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")
_IPV4 = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_IPV6 = re.compile(r"\b(?:[A-Fa-f0-9]{1,4}:){2,7}[A-Fa-f0-9]{1,4}\b")
_SHA256 = re.compile(r"\b[A-Fa-f0-9]{64}\b")
_SHA1 = re.compile(r"\b[A-Fa-f0-9]{40}\b")
_MD5 = re.compile(r"\b[A-Fa-f0-9]{32}\b")
# A dotted hostname with a plausible TLD; validated further against a small non-TLD deny-set.
_DOMAIN = re.compile(r"\b(?:[A-Za-z0-9](?:[A-Za-z0-9\-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,24}\b")

# Common file extensions that look like domains (``report.docx``) but are not indicators.
_FILE_EXT = frozenset(
    {
        "exe",
        "dll",
        "docx",
        "doc",
        "xlsx",
        "xls",
        "pdf",
        "zip",
        "rar",
        "js",
        "ps1",
        "bin",
        "png",
        "jpg",
        "txt",
        "html",
        "php",
        "py",
        "sh",
        "bat",
        "lnk",
        "iso",
        "img",
        "gz",
        "log",
        "csv",
    }
)


@dataclass(frozen=True, slots=True)
class Indicator:
    """A single extracted indicator. ``value`` is normalised; ``defanged`` is safe to display."""

    kind: IOCKind
    value: str
    defanged: str


def refang(text: str) -> str:
    """Reverse common defanging so real indicators can be matched."""
    for pattern, repl in _REFANG:
        text = pattern.sub(repl, text)
    return text


def defang(kind: IOCKind, value: str) -> str:
    """Render an indicator inert for display (no live links / resolvable hosts)."""
    if kind in ("ipv4", "domain"):
        return value.replace(".", "[.]")
    if kind == "email":
        return value.replace("@", "[at]").replace(".", "[.]")
    if kind == "url":
        out = value.replace("http", "hxxp", 1) if value.lower().startswith("http") else value
        return out.replace(".", "[.]")
    return value


def _valid_ipv4(value: str) -> bool:
    try:
        ipaddress.IPv4Address(value)
    except ValueError:
        return False
    return True


def _valid_ipv6(value: str) -> bool:
    try:
        ipaddress.IPv6Address(value)
    except ValueError:
        return False
    return True


def _looks_like_domain(value: str) -> bool:
    tld = value.rsplit(".", 1)[-1].lower()
    return tld not in _FILE_EXT and not tld.isdigit()


def _hosts_from_urls(urls: Iterable[str]) -> set[str]:
    hosts: set[str] = set()
    for url in urls:
        m = re.match(r"https?://([^/:?#]+)", url, re.I)
        if m:
            hosts.add(m.group(1).lower())
    return hosts


def extract(text: str) -> list[Indicator]:
    """Extract unique indicators from advisory text, de-duplicated and ordered by ``KINDS``.

    Overlaps are resolved so each substring is reported once at its most specific kind: URL
    hosts and email domains are not also emitted as bare domains, and a 64-hex string is a
    SHA-256 (never an MD5 substring).
    """
    refanged = refang(text)
    found: dict[tuple[str, str], Indicator] = {}

    def add(kind: IOCKind, value: str) -> None:
        found.setdefault((kind, value), Indicator(kind, value, defang(kind, value)))

    urls = _URL.findall(refanged)
    for url in urls:
        add("url", url.rstrip(".,);]"))
    for cve in _CVE.findall(refanged):
        add("cve", cve.upper())
    emails = _EMAIL.findall(refanged)
    for email in emails:
        add("email", email.lower())
    for ip in _IPV4.findall(refanged):
        if _valid_ipv4(ip):
            add("ipv4", ip)
    for ip in _IPV6.findall(refanged):
        if _valid_ipv6(ip):
            add("ipv6", ip.lower())
    for h in _SHA256.findall(refanged):
        add("sha256", h.lower())
    matched_hashes = {v for (k, v) in found if k == "sha256"}
    for h in _SHA1.findall(refanged):
        add("sha1", h.lower())
    for h in _MD5.findall(refanged):
        # 32-hex inside a 40/64-hex string is not an independent MD5.
        if not any(h.lower() in longer for longer in matched_hashes):
            add("md5", h.lower())

    # Domains last: exclude hosts already captured via URLs/emails and non-indicator filenames.
    exclude = _hosts_from_urls(urls) | {e.split("@", 1)[1] for e in (x.lower() for x in emails)}
    for dom in _DOMAIN.findall(refanged):
        low = dom.lower()
        if low in exclude or not _looks_like_domain(low):
            continue
        if _valid_ipv4(dom):  # already handled as ipv4
            continue
        add("domain", low)

    order = {k: i for i, k in enumerate(KINDS)}
    return sorted(found.values(), key=lambda ind: (order[ind.kind], ind.value))
