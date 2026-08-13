"""Tests for Ed25519 plugin signing, verification, tamper detection, trust + revocation."""

from __future__ import annotations

import pytest
from dula_plugins.connectors.siem import siem_manifest
from dula_plugins.manifest import Capability, PluginManifest, SideEffect
from dula_plugins.signing import (
    SignatureError,
    TrustStore,
    generate_keypair,
    sign_manifest,
    verify_plugin,
)


def _trust_for(key_id: str, public_bytes: bytes) -> TrustStore:
    trust = TrustStore()
    trust.trust(key_id, public_bytes)
    return trust


def test_sign_and_verify_roundtrip() -> None:
    private, public = generate_keypair()
    manifest = siem_manifest()
    signed = sign_manifest(manifest, private)
    verify_plugin(signed, _trust_for(manifest.publisher_key_id, public))  # no raise


def test_untrusted_key_is_rejected() -> None:
    private, _public = generate_keypair()
    signed = sign_manifest(siem_manifest(), private)
    with pytest.raises(SignatureError, match="not trusted"):
        verify_plugin(signed, TrustStore())  # empty trust store


def test_tampered_manifest_fails_verification() -> None:
    private, public = generate_keypair()
    manifest = siem_manifest()
    signed = sign_manifest(manifest, private)
    # Tamper: swap in a manifest with an extra (privilege-adding) capability, same signature.
    tampered = signed.__class__(
        manifest=manifest.model_copy(
            update={
                "capabilities": [
                    *manifest.capabilities,
                    Capability(
                        name="siem.delete",
                        side_effect=SideEffect.CONSEQUENTIAL,
                        permission="connector.siem.delete",
                    ),
                ]
            }
        ),
        signature=signed.signature,
    )
    with pytest.raises(SignatureError, match=r"tampered|does not match"):
        verify_plugin(tampered, _trust_for(manifest.publisher_key_id, public))


def test_wrong_key_fails_verification() -> None:
    private_a, _ = generate_keypair()
    _, public_b = generate_keypair()
    signed = sign_manifest(siem_manifest(), private_a)
    with pytest.raises(SignatureError):
        verify_plugin(signed, _trust_for(siem_manifest().publisher_key_id, public_b))


def test_revocation_removes_trust() -> None:
    private, public = generate_keypair()
    manifest = siem_manifest()
    signed = sign_manifest(manifest, private)
    trust = _trust_for(manifest.publisher_key_id, public)
    verify_plugin(signed, trust)  # ok
    trust.revoke(manifest.publisher_key_id)
    with pytest.raises(SignatureError, match="not trusted"):
        verify_plugin(signed, trust)


def test_malformed_signature_rejected() -> None:
    _, public = generate_keypair()
    manifest = siem_manifest()
    from dula_plugins.signing import SignedPlugin

    bad = SignedPlugin(manifest=manifest, signature="!!not-base64!!")
    with pytest.raises(SignatureError, match="malformed"):
        verify_plugin(bad, _trust_for(manifest.publisher_key_id, public))


def test_canonical_bytes_are_deterministic() -> None:
    m = PluginManifest(
        id="dula-plugin-acme-widget",
        version="1.2.3",
        publisher_key_id="acme",
        capabilities=[Capability(name="acme.ping", side_effect=SideEffect.READ, permission="p")],
    )
    assert m.canonical_bytes() == m.model_copy().canonical_bytes()
