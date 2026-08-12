"""Shared Dula utilities: config, logging, telemetry, OIDC auth, OPA, and events.

See docs/00-Governance/CodingStandards.md and docs/12-API/Authentication.md.
"""

from dula_common.auth import AuthError, OIDCVerifier, TokenClaims
from dula_common.config import CommonSettings
from dula_common.events import EventEnvelope, EventPublisher, decode_envelope
from dula_common.logging import configure_logging
from dula_common.opa import OPAClient

__all__ = [
    "AuthError",
    "CommonSettings",
    "EventEnvelope",
    "EventPublisher",
    "OIDCVerifier",
    "OPAClient",
    "TokenClaims",
    "configure_logging",
    "decode_envelope",
]
