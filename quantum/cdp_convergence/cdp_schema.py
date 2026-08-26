#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CDP Schema — quantum/cdp_convergence

websocket_ready defaults False until OAuth 2.0 bearer validation succeeds.
FAL ternary (−1/0/+1) is derived from websocket/oauth/foreign-trace state.
Seal: ∀∞φ² · CDP_SCHEMA_FAL · WOOD_DRAGON_0.91 · SEALED
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional
import time

DEFAULT_HARMONY = 0.7337473231


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
    # FAL / Port-380 ternary merge
    fal_ternary: int = 0  # default nullify while unauthenticated
    harmony_in: float = DEFAULT_HARMONY
    harmony_out: float = 0.0
    fal_mode: str = "nullify"
    ts: float = field(default_factory=time.time)

    def apply_fal(self) -> "CdpStatus":
        """Derive FAL ternary from CDP/OAuth fields and scale harmony."""
        try:
            from quantum.radar_lindblad.port_380_gate import evaluate_gate
        except ImportError:
            try:
                from radar_lindblad.port_380_gate import evaluate_gate  # type: ignore
            except ImportError:
                # Soft local fallback mirroring FAL rules
                if self.foreign_model_trace:
                    t = -1
                elif not self.websocket_ready or not self.oauth_validated:
                    t = 0
                else:
                    t = 1
                hout = (
                    self.harmony_in
                    if t == 1
                    else (-self.harmony_in if t == -1 else 0.0)
                )
                self.fal_ternary = t
                self.harmony_out = hout
                self.fal_mode = {1: "identity", 0: "nullify", -1: "invert"}[t]
                return self

        result = evaluate_gate(
            self.harmony_in,
            websocket_ready=self.websocket_ready,
            oauth_validated=self.oauth_validated,
            foreign_model_trace=self.foreign_model_trace,
        )
        self.fal_ternary = int(result["ternary"])
        self.harmony_out = float(result["harmony_out"])
        self.fal_mode = str(result["mode"])
        return self

    def to_dict(self) -> Dict[str, Any]:
        self.apply_fal()
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
