#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Browser bridge handshake protocol for CDP (quantum/cdp_convergence).

Contract:
  websocket_ready is FALSE until OAuth 2.0 validation succeeds.
  On success: session_id minted, latency recorded, websocket_ready=True.

Seal: ∀∞φ² · CDP_HANDSHAKE_OAUTH · WOOD_DRAGON_0.91 · SEALED
"""
from __future__ import annotations

import hashlib
import time
from typing import Optional, Tuple

from .cdp_schema import CdpStatus, OAuth2TokenClaims
from . import oauth2


def _session_id_from_token(token: str) -> str:
    digest = hashlib.sha256(token.encode()).hexdigest()[:16]
    return f"cdp_{digest}"


def handshake_from_authorization(
    authorization: Optional[str],
    *,
    handover_started: Optional[float] = None,
) -> CdpStatus:
    """
    Validate Bearer token; only then set websocket_ready=True.
    """
    t0 = handover_started if handover_started is not None else time.perf_counter()
    claims, err = oauth2.validate_bearer(authorization)
    latency_ms = (time.perf_counter() - t0) * 1000.0

    if err or claims is None or not claims.valid:
        return CdpStatus(
            handover_latency_ms=latency_ms,
            websocket_ready=False,
            oauth_validated=False,
            error=err or "oauth validation failed",
            source="quantum.cdp_convergence.handshake",
        )

    return CdpStatus(
        handover_latency_ms=latency_ms,
        websocket_ready=True,
        session_id=_session_id_from_token(claims.access_token),
        oauth_validated=True,
        oauth_issuer=claims.issuer,
        oauth_subject=claims.subject,
        oauth_expires_at=claims.expires_at,
        source="quantum.cdp_convergence.handshake",
    )


def handshake_client_credentials(
    scope: str = "cdp.handshake",
) -> Tuple[CdpStatus, Optional[OAuth2TokenClaims]]:
    """
    Acquire token via client_credentials, then open CDP session.
    websocket_ready stays False if token grant fails.
    """
    t0 = time.perf_counter()
    claims, err = oauth2.fetch_client_credentials(scope=scope)
    latency_ms = (time.perf_counter() - t0) * 1000.0

    if err or claims is None or not claims.valid:
        return (
            CdpStatus(
                handover_latency_ms=latency_ms,
                websocket_ready=False,
                oauth_validated=False,
                error=err or "client_credentials failed",
                source="quantum.cdp_convergence.handshake",
            ),
            None,
        )

    status = CdpStatus(
        handover_latency_ms=latency_ms,
        websocket_ready=True,
        session_id=_session_id_from_token(claims.access_token),
        oauth_validated=True,
        oauth_issuer=claims.issuer,
        oauth_subject=claims.subject,
        oauth_expires_at=claims.expires_at,
        source="quantum.cdp_convergence.handshake",
    )
    return status, claims


def status_unauthenticated() -> CdpStatus:
    """Explicit false websocket field — default quantum surface."""
    return CdpStatus(
        handover_latency_ms=0.0,
        websocket_ready=False,
        oauth_validated=False,
        error="no OAuth 2.0 credentials presented",
        source="quantum.cdp_convergence.handshake",
    )
