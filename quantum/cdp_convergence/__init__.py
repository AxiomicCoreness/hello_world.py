"""CDP Convergence quadrant — OAuth 2.0 gates websocket_ready + VOID-QCH.

Public surface (name → submodule):

    CdpStatus, OAuth2TokenClaims, CdpSession        ← .cdp_schema
    handshake_client_credentials,
    handshake_from_authorization,
    status_unauthenticated                          ← .handshake
    oauth2                                          ← .oauth2 (module)
    chemical_precision_feasibility,
    validate_progression,
    build_progression,
    VoidQCHReport                                   ← .void_qch
    require_websocket_ready,
    WebSocketGateError                              ← .websocket_gate

Import style is lazy: `import quantum.cdp_convergence` succeeds even
if a submodule has a transient import error. The failing name only
raises when first accessed.
"""
from __future__ import annotations

import importlib
from typing import Any

__version__ = "0.1.0"

_EXPORTS = {
    # --- schema ---
    "CdpStatus":                    ("cdp_schema",     "CdpStatus"),
    "OAuth2TokenClaims":            ("cdp_schema",     "OAuth2TokenClaims"),
    "CdpSession":                   ("cdp_schema",     "CdpSession"),

    # --- handshake ---
    "handshake_client_credentials": ("handshake",      "handshake_client_credentials"),
    "handshake_from_authorization": ("handshake",      "handshake_from_authorization"),
    "status_unauthenticated":       ("handshake",      "status_unauthenticated"),

    # --- oauth2 (module) ---
    "oauth2":                       ("oauth2",         None),

    # --- void_qch ---
    "chemical_precision_feasibility": ("void_qch",     "chemical_precision_feasibility"),
    "validate_progression":           ("void_qch",     "validate_progression"),
    "build_progression":              ("void_qch",     "build_progression"),
    "VoidQCHReport":                  ("void_qch",     "VoidQCHReport"),

    # --- websocket_gate ---
    "require_websocket_ready":        ("websocket_gate", "require_websocket_ready"),
    "WebSocketGateError":             ("websocket_gate", "WebSocketGateError"),
}

__all__ = list(_EXPORTS.keys())


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    submodule_name, attr_name = _EXPORTS[name]
    full = f"{__name__}.{submodule_name}"
    mod = importlib.import_module(full)
    if attr_name is None:
        return mod
    return getattr(mod, attr_name)


def __dir__():
    return sorted(set(__all__) | {"__version__"})
