#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OAuth 2.0 helpers for CDP convergence (quantum folder).

Supports:
  - client_credentials grant against OIDC_TOKEN_URL / OAUTH_TOKEN_URL
  - bearer validation of an inbound Authorization header
  - offline/dev token when OAUTH_OFFLINE=1 (still explicit — not silent true)

Rule: websocket_ready remains False until a valid token is established.
Seal: ∀∞φ² · CDP_OAUTH2 · WOOD_DRAGON_0.91 · SEALED
SACL wire: validate_bearer_garden (Entry 8949) — garden offline HMAC + JWKS JWT
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional, Tuple

from .cdp_schema import OAuth2TokenClaims


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def token_endpoint() -> str:
    return _env("OIDC_TOKEN_URL") or _env("OAUTH_TOKEN_URL") or _env(
        "OIDC_ISSUER", ""
    ).rstrip("/") + ("/oauth/token" if _env("OIDC_ISSUER") else "")


def client_id() -> str:
    return _env("OIDC_CLIENT_ID") or _env("OAUTH_CLIENT_ID")


def client_secret() -> str:
    return _env("OIDC_CLIENT_SECRET") or _env("OAUTH_CLIENT_SECRET")


def offline_mode() -> bool:
    v = _env("OAUTH_OFFLINE", _env("CDP_OAUTH_OFFLINE", _env("OIDC_OFFLINE", "0"))).lower()
    return v in {"1", "true", "yes", "on"}


def mint_offline_claims(subject: str = "garden-offline") -> OAuth2TokenClaims:
    """Deterministic offline bearer for local distill / CI — still explicit."""
    raw = f"offline:{subject}:{int(time.time() // 3600)}".encode()
    token = "off_" + hashlib.sha256(raw).hexdigest()[:32]
    return OAuth2TokenClaims(
        access_token=token,
        token_type="Bearer",
        expires_in=3600,
        scope="cdp.handshake offline",
        issuer="local/oauth_offline",
        subject=subject,
    )


def fetch_client_credentials(
    scope: str = "cdp.handshake",
    timeout_s: float = 8.0,
) -> Tuple[Optional[OAuth2TokenClaims], Optional[str]]:
    """
    OAuth 2.0 client_credentials grant.
    Returns (claims, error). On success claims.valid is True.
    """
    if offline_mode():
        return mint_offline_claims(), None

    url = token_endpoint()
    cid = client_id()
    secret = client_secret()
    if not url or not cid or not secret:
        return None, (
            "OAuth 2.0 not configured: set OIDC_TOKEN_URL (or OAUTH_TOKEN_URL), "
            "OIDC_CLIENT_ID, OIDC_CLIENT_SECRET — or OAUTH_OFFLINE=1"
        )

    body = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": cid,
            "client_secret": secret,
            "scope": scope,
        }
    ).encode()

    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:240]
        return None, f"token endpoint HTTP {e.code}: {detail}"
    except Exception as e:
        return None, f"token endpoint error: {e}"

    access = str(payload.get("access_token") or "")
    if not access:
        return None, "token endpoint returned no access_token"

    claims = OAuth2TokenClaims(
        access_token=access,
        token_type=str(payload.get("token_type") or "Bearer"),
        expires_in=int(payload.get("expires_in") or 3600),
        scope=str(payload.get("scope") or scope),
        issuer=_env("OIDC_ISSUER") or url,
        subject=str(payload.get("sub") or cid),
    )
    return claims, None


def validate_bearer(
    authorization_header: Optional[str],
    expected_prefix: str = "Bearer ",
) -> Tuple[Optional[OAuth2TokenClaims], Optional[str]]:
    """
    Validate inbound Authorization: Bearer <token>.
    Offline mode accepts tokens starting with off_ minted by mint_offline_claims.
    Live mode requires non-empty bearer; optional introspect if OAUTH_INTROSPECT_URL set.
    """
    if not authorization_header:
        return None, "missing Authorization header"

    hdr = authorization_header.strip()
    if not hdr.lower().startswith(expected_prefix.lower()):
        return None, "Authorization must be Bearer scheme"

    token = hdr[len(expected_prefix) :].strip()
    if not token:
        return None, "empty bearer token"

    if offline_mode():
        if token.startswith("off_"):
            return OAuth2TokenClaims(
                access_token=token,
                issuer="local/oauth_offline",
                subject="garden-offline",
                scope="cdp.handshake offline",
            ), None
        if _env("OAUTH_OFFLINE_PERMISSIVE", "0") in {"1", "true"}:
            return OAuth2TokenClaims(
                access_token=token,
                issuer="local/oauth_offline_permissive",
                subject="permissive",
            ), None
        return None, "offline mode requires off_* token (or OAUTH_OFFLINE_PERMISSIVE=1)"

    introspect = _env("OAUTH_INTROSPECT_URL")
    if introspect:
        return _introspect(token, introspect)

    return OAuth2TokenClaims(
        access_token=token,
        issuer=_env("OIDC_ISSUER") or "configured",
        subject="bearer",
        scope="cdp.handshake",
    ), None


def _introspect(
    token: str, url: str, timeout_s: float = 8.0
) -> Tuple[Optional[OAuth2TokenClaims], Optional[str]]:
    cid, secret = client_id(), client_secret()
    body = urllib.parse.urlencode({"token": token}).encode()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }
    if cid and secret:
        basic = base64.b64encode(f"{cid}:{secret}".encode()).decode()
        headers["Authorization"] = f"Basic {basic}"
    req = urllib.request.Request(url, data=body, method="POST", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            payload = json.loads(resp.read().decode() or "{}")
    except Exception as e:
        return None, f"introspect error: {e}"

    if not payload.get("active"):
        return None, "token inactive per introspection"

    return OAuth2TokenClaims(
        access_token=token,
        token_type="Bearer",
        expires_in=int(payload.get("exp", time.time() + 3600) - time.time()),
        scope=str(payload.get("scope") or "cdp.handshake"),
        issuer=str(payload.get("iss") or _env("OIDC_ISSUER")),
        subject=str(payload.get("sub") or ""),
    ), None


# ── SACL / Entry 8949: Garden OIDC cloud bearer ────────────────────────────

def validate_bearer_garden(
    authorization_header: Optional[str],
) -> Tuple[Optional[OAuth2TokenClaims], Optional[str]]:
    """
    Extended bearer gate for /oidc_handover and CDP handshake:

      1) validate_bearer (off_* + live / introspect)
      2) quantum.security.oidc_cloud offline HMAC tokens
      3) JWT verified via JWKS cache when OIDC_ISSUER is set

    batch_oidc_tokenizer is intentionally not modified.
    """
    claims, err = validate_bearer(authorization_header)
    if claims is not None:
        return claims, None

    if not authorization_header:
        return None, err or "missing Authorization header"
    hdr = authorization_header.strip()
    if not hdr.lower().startswith("bearer "):
        return None, err or "Authorization must be Bearer scheme"
    token = hdr[7:].strip()
    if not token:
        return None, "empty bearer token"

    try:
        from quantum.security.oidc_cloud import verify_offline_token

        oc = verify_offline_token(token)
        return (
            OAuth2TokenClaims(
                access_token=token,
                token_type="Bearer",
                expires_in=max(0, oc.exp - int(time.time())),
                scope="cdp.handshake garden.offline",
                issuer=oc.iss,
                subject=oc.sub,
            ),
            None,
        )
    except Exception:
        pass

    issuer = _env("OIDC_ISSUER")
    if issuer and token.count(".") == 2:
        try:
            from quantum.security.jwks_cache import get_jwks_cache
            from quantum.security.oidc_cloud import verify_jwt, decode_jwt_unverified

            header = decode_jwt_unverified(token)["header"]
            kid = header.get("kid")
            entry = get_jwks_cache().get(issuer, kid=kid)
            oc = verify_jwt(
                token,
                issuer=issuer,
                audience=_env("OIDC_AUDIENCE") or None,
                jwks=entry.jwks,
            )
            if not oc.verified and not offline_mode():
                return None, "JWT signature not verified"
            return (
                OAuth2TokenClaims(
                    access_token=token,
                    token_type="Bearer",
                    expires_in=max(0, oc.exp - int(time.time())),
                    scope="cdp.handshake oidc.jwt",
                    issuer=oc.iss,
                    subject=oc.sub,
                ),
                None,
            )
        except Exception as e:
            return None, f"JWT/JWKS validation failed: {e}"

    return None, err or "bearer validation failed"
