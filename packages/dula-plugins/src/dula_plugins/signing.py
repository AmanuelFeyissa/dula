"""Plugin signing + verification (docs/14-Plugins/PluginSecurity.md §1, PluginLifecycle.md §2).

Provenance is established with **Ed25519**: a publisher signs the manifest's canonical bytes with
their private key, and the host verifies the signature against a **trust store** of known public
keys before install. This is the "Verify" lifecycle gate — an unsigned plugin, a tampered
manifest, or a signature from an untrusted/unknown key is rejected. Keys are referenced by
``publisher_key_id`` so trust can be granted and **revoked** per publisher.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass, field

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from dula_plugins.manifest import PluginManifest


@dataclass(frozen=True, slots=True)
class SignedPlugin:
    """A manifest plus a detached signature over its canonical bytes."""

    manifest: PluginManifest
    signature: str  # base64-encoded Ed25519 signature


def generate_keypair() -> tuple[Ed25519PrivateKey, bytes]:
    """Return a new (private key, raw public-key bytes) pair."""
    private = Ed25519PrivateKey.generate()
    public_bytes = private.public_key().public_bytes_raw()
    return private, public_bytes


def sign_manifest(manifest: PluginManifest, private_key: Ed25519PrivateKey) -> SignedPlugin:
    signature = private_key.sign(manifest.canonical_bytes())
    return SignedPlugin(manifest=manifest, signature=base64.b64encode(signature).decode("ascii"))


@dataclass
class TrustStore:
    """Trusted publisher public keys, by ``publisher_key_id``. Supports revocation."""

    _keys: dict[str, bytes] = field(default_factory=dict)

    def trust(self, key_id: str, public_key_bytes: bytes) -> None:
        self._keys[key_id] = public_key_bytes

    def revoke(self, key_id: str) -> None:
        self._keys.pop(key_id, None)

    def is_trusted(self, key_id: str) -> bool:
        return key_id in self._keys

    def public_key(self, key_id: str) -> Ed25519PublicKey | None:
        raw = self._keys.get(key_id)
        return Ed25519PublicKey.from_public_bytes(raw) if raw is not None else None


class SignatureError(Exception):
    """Raised when a plugin signature is missing, malformed, untrusted, or invalid."""


def verify_plugin(signed: SignedPlugin, trust: TrustStore) -> None:
    """Verify a signed plugin against the trust store; raise :class:`SignatureError` on failure.

    Fails closed: an untrusted key id, a malformed signature, or a signature that does not match
    the manifest's canonical bytes (i.e. tampering) all raise.
    """
    key_id = signed.manifest.publisher_key_id
    public_key = trust.public_key(key_id)
    if public_key is None:
        raise SignatureError(f"publisher key '{key_id}' is not trusted")
    try:
        signature = base64.b64decode(signed.signature, validate=True)
    except (ValueError, TypeError) as exc:
        raise SignatureError("malformed signature encoding") from exc
    try:
        public_key.verify(signature, signed.manifest.canonical_bytes())
    except InvalidSignature as exc:
        raise SignatureError("signature does not match manifest (tampered or wrong key)") from exc
