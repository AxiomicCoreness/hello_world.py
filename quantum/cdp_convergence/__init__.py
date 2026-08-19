"""CDP Convergence quadrant — OAuth 2.0 gates websocket_ready + VOID-QCH."""

from .cdp_schema import CdpStatus, OAuth2TokenClaims
from .handshake import (
    handshake_client_credentials,
    handshake_from_authorization,
    status_unauthenticated,
)
from . import oauth2
from .void_qch import (
    chemical_precision_feasibility,
    validate_progression,
    build_progression,
    VoidQCHReport,
)

__all__ = [
    "CdpStatus",
    "OAuth2TokenClaims",
    "handshake_client_credentials",
    "handshake_from_authorization",
    "status_unauthenticated",
    "oauth2",
    "chemical_precision_feasibility",
    "validate_progression",
    "build_progression",
    "VoidQCHReport",
]
