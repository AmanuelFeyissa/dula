"""Tests for IOC extraction, refang/defang, and overlap resolution."""

from __future__ import annotations

from dula_ai.intel.iocs import defang, extract, refang


def _values(text: str, kind: str) -> list[str]:
    return [i.value for i in extract(text) if i.kind == kind]


def test_refang_normalizes_defanged_indicators() -> None:
    assert refang("hxxps://evil[.]com/a") == "https://evil.com/a"
    assert refang("1[.]2[.]3[.]4") == "1.2.3.4"
    assert refang("user[at]corp[.]com") == "user@corp.com"


def test_extract_ipv4_valid_only() -> None:
    assert _values("contact 8.8.8.8 not 999.1.1.1", "ipv4") == ["8.8.8.8"]


def test_extract_defanged_domain_and_url() -> None:
    result = extract("beacon to hxxp://bad[.]example[.]com/payload and c2 at evil[.]net")
    urls = [i for i in result if i.kind == "url"]
    domains = [i.value for i in result if i.kind == "domain"]
    assert urls and urls[0].value.startswith("http://bad.example.com")
    # The URL host is not also reported as a bare domain; the standalone C2 domain is.
    assert "bad.example.com" not in domains
    assert "evil.net" in domains


def test_hash_kinds_do_not_overlap() -> None:
    sha256 = "a" * 64
    md5 = "b" * 32
    result = extract(f"hashes {sha256} and {md5}")
    kinds = {(i.kind, i.value) for i in result}
    assert ("sha256", sha256) in kinds
    assert ("md5", md5) in kinds
    # The 32-hex prefix of the 64-hex string is not a separate MD5.
    assert ("md5", "a" * 32) not in kinds


def test_cve_and_email_extracted() -> None:
    result = extract("See CVE-2024-1234 reported by analyst@corp.com")
    assert ("cve", "CVE-2024-1234") in {(i.kind, i.value) for i in result}
    assert "analyst@corp.com" in _values("x analyst@corp.com y", "email")
    # The email's domain is not double-reported as a bare domain.
    assert "corp.com" not in _values("analyst@corp.com", "domain")


def test_filename_not_treated_as_domain() -> None:
    assert _values("dropped report.docx and update.exe", "domain") == []


def test_defang_is_inert() -> None:
    assert defang("domain", "evil.com") == "evil[.]com"
    assert defang("url", "http://evil.com") == "hxxp://evil[.]com"
    assert defang("email", "a@b.com") == "a[at]b[.]com"


def test_extraction_is_deterministic_and_deduped() -> None:
    text = "8.8.8.8 8.8.8.8 evil.com evil.com"
    first = extract(text)
    assert first == extract(text)
    assert len([i for i in first if i.value == "8.8.8.8"]) == 1
