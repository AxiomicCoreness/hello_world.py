#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CDP Schema — quantum/cdp_convergence

websocket_ready defaults False until OAuth 2.0 bearer validation succeeds.
Seal: ∀∞φ² · CDP_SCHEMA_OAUTH · WOOD_DRAGON_0.91 · SEALED
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional
import time


@dataclass
class CdpStatus:
    """Canonical CDP status consumed by src/cdp_distill.ts distillTree."""

    handover_latency_ms: float = 999.0
    websocket_ready: bool = False  # FALSE until OAuth 2.0 validates
    session_id: Optional[str] = None
    foreign_model_trace: Optional[str] = None
    phi_phase_deg: float = 202.6
    coherence: float = 1.0
    source: str = "quantum.cdp_convergence"
    oauth_validated: bool = False
    oauth_issuer: Optional[str] = None
    oauth_subject: Optional[str] = None
    oauth_expires_at: Optional[float] = None
    error: Optional[str] = None
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OAuth2TokenClaims:
    """Minimal OAuth 2.0 access-token claims used for CDP gate."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    scope: str = "cdp.handshake"
    issuer: str = ""
    subject: str = ""
    obtained_at: float = field(default_factory=time.time)

    @property
    def expires_at(self) -> float:
        return self.obtained_at + float(self.expires_in)

    @property
    def valid(self) -> bool:
        return bool(self.access_token) and time.time() < self.expires_at
