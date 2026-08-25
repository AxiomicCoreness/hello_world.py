#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ OIDC CLOUD PROVIDERS — ENTRY 8944

Federated identity for cloud providers without long-lived static keys.

Providers:
  - github   : GitHub Actions OIDC (ACTIONS_ID_TOKEN_REQUEST_*)
  - aws      : STS AssumeRoleWithWebIdentity
  - gcp      : STS token exchange → access token (Workload Identity Federation)
  - azure    : OAuth2 client_credentials with federated assertion
  - generic  : discover JWKS from issuer, verify JWT (RS256/ES256 when crypto present)

Offline / Garden mode:
  OIDC_OFFLINE=1 → mint local HMAC-bound claims (no network), compatible with
  batch_oidc_tokenizer semantics (full 64-char digests, never truncated).

Seal: ∀∞φ² · OIDC_CLOUD_8944 · WOOD_DRAGON_0.91 · SEALED
Witness: 8943 → 8944 — UNBROKEN
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import math
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
ENTRY = 8944
SEAL = "∀∞φ² · OIDC_CLOUD_8944 · WOOD_DRAGON_0.91 · SEALED"
LOG = logging.getLogger("oidc_cloud")

# ─── Cryptography ─────────────────────────────────────────────────────
try:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding, ec, rsa
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    LOG.warning("cryptography not installed; JWT verification disabled")


class CloudProvider(str, Enum):
    GITHUB = "github"
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    GENERIC = "generic"
    OFFLINE = "offline"


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def offline_mode() -> bool:
    v = _env("OIDC_OFFLINE", _env("OAUTH_OFFLINE", "0")).lower()
    return v in {"1", "true", "yes", "on"}


def _b64url_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def _http_json(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    body: Optional[bytes] = None,
    timeout: float = 15.0,
) -> Tuple[int, Dict[str, Any]]:
    req = urllib.request.Request(url, data=body, method=method)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw else {"error": str(e)}
        except json.JSONDecodeError:
            payload = {"error": raw or str(e)}
        return e.code, payload
    except Exception as e:
        return 0, {"error": str(e)}


@dataclass
class OIDCClaims:
    sub: str
    iss: str
    aud: Any
    exp: int
    iat: int
    provider: str
    raw: Dict[str, Any] = field(default_factory=dict)
    verified: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FederatedCredential:
    provider: str
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    expires_at: float = 0.0
    claims: Optional[OIDCClaims] = None
    meta: Dict[str, Any] = field(default_factory=dict)
    seal: str = SEAL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
            "expires_at": self.expires_at,
            "access_token_prefix": (self.access_token[:12] + "…") if self.access_token else "",
            "access_token_len": len(self.access_token or ""),
            "claims": self.claims.to_dict() if self.claims else None,
            "meta": self.meta,
            "seal": self.seal,
            "entry": ENTRY,
        }


def decode_jwt_unverified(token: str) -> Dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("not a JWT (expected 3 segments)")
    header = json.loads(_b64url_decode(parts[0]))
    payload = json.loads(_b64url_decode(parts[1]))
    return {"header": header, "payload": payload, "signature": parts[2]}


def discover_jwks_uri(issuer: str) -> str:
    issuer = issuer.rstrip("/")
    status, doc = _http_json(f"{issuer}/.well-known/openid-configuration")
    if status == 200 and doc.get("jwks_uri"):
        return str(doc["jwks_uri"])
    if "token.actions.githubusercontent.com" in issuer:
        return "https://token.actions.githubusercontent.com/.well-known/jwks"
    raise RuntimeError(f"cannot discover jwks_uri for issuer={issuer} status={status}")


def fetch_jwks(jwks_uri: str, cache_path: Optional[Path] = None) -> Dict[str, Any]:
    status, body = _http_json(jwks_uri)
    if status != 200:
        raise RuntimeError(f"JWKS fetch failed status={status} body={body}")
    path = cache_path or Path(_env("OIDC_JWKS_CACHE", ".oidc_jwks.json"))
    try:
        path.write_text(json.dumps(body, indent=2), encoding="utf-8")
    except Exception as e:
        LOG.warning("JWKS cache write failed: %s", e)
    return body


def _public_key_from_jwk(jwk: Dict[str, Any]):
    if not CRYPTO_AVAILABLE:
        raise RuntimeError("cryptography required for JWT signature verify")
    kty = jwk.get("kty")
    if kty == "RSA":
        n = int.from_bytes(_b64url_decode(jwk["n"]), "big")
        e = int.from_bytes(_b64url_decode(jwk["e"]), "big")
        return rsa.RSAPublicNumbers(e, n).public_key(default_backend())
    if kty == "EC":
        curves = {"P-256": ec.SECP256R1(), "P-384": ec.SECP384R1(), "P-521": ec.SECP521R1()}
        curve = curves.get(jwk.get("crv", "P-256"))
        if curve is None:
            raise ValueError(f"unsupported EC curve {jwk.get('crv')}")
        x = int.from_bytes(_b64url_decode(jwk["x"]), "big")
        y = int.from_bytes(_b64url_decode(jwk["y"]), "big")
        return ec.EllipticCurvePublicNumbers(x, y, curve).public_key(default_backend())
    raise ValueError(f"unsupported kty={kty}")


def verify_jwt(
    token: str,
    *,
    issuer: Optional[str] = None,
    audience: Optional[str] = None,
    jwks: Optional[Dict[str, Any]] = None,
    leeway: float = 60.0,
) -> OIDCClaims:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("malformed JWT")
    header = json.loads(_b64url_decode(parts[0]))
    payload = json.loads(_b64url_decode(parts[1]))
    signing_input = f"{parts[0]}.{parts[1]}".encode("ascii")
    signature = _b64url_decode(parts[2])

    iss = str(payload.get("iss") or issuer or "")
    if issuer and payload.get("iss") and payload["iss"] != issuer:
        raise ValueError(f"issuer mismatch: {payload.get('iss')} != {issuer}")
    if audience is not None:
        aud = payload.get("aud")
        if isinstance(aud, list):
            if audience not in aud:
                raise ValueError("audience mismatch")
        elif aud != audience:
            raise ValueError("audience mismatch")

    now = time.time()
    exp = int(payload.get("exp", 0))
    if exp and now > exp + leeway:
        raise ValueError("token expired")
    nbf = int(payload.get("nbf", 0))
    if nbf and now + leeway < nbf:
        raise ValueError("token not yet valid")

    verified = False
    if CRYPTO_AVAILABLE and jwks:
        kid = header.get("kid")
        keys = jwks.get("keys") or []
        candidates = [k for k in keys if not kid or k.get("kid") == kid] or keys
        alg = header.get("alg", "RS256")
        last_err: Optional[Exception] = None
        for jwk in candidates:
            try:
                pub = _public_key_from_jwk(jwk)
                if alg.startswith("RS"):
                    pub.verify(signature, signing_input, padding.PKCS1v15(), hashes.SHA256())
                elif alg.startswith("ES"):
                    pub.verify(signature, signing_input, ec.ECDSA(hashes.SHA256()))
                else:
                    raise ValueError(f"unsupported alg {alg}")
                verified = True
                break
            except Exception as e:
                last_err = e
                continue
        if not verified and last_err:
            raise ValueError(f"signature verification failed: {last_err}")
    elif not CRYPTO_AVAILABLE:
        LOG.warning("cryptography missing — JWT signature not verified (claims only)")
    else:
        LOG.warning("no JWKS provided — JWT signature not verified")

    return OIDCClaims(
        sub=str(payload.get("sub", "")),
        iss=iss,
        aud=payload.get("aud"),
        exp=exp,
        iat=int(payload.get("iat", 0)),
        provider=CloudProvider.GENERIC.value,
        raw=payload,
        verified=verified,
    )


def resolve_offline_secret() -> str:
    env = _env("OIDC_CLIENT_SECRET") or _env("GARDEN_SECRET")
    if env and len(env) >= 32:
        return env
    seed = f"GARDEN_OIDC_OFFLINE_{int(time.time() // 3600)}_{PHI}"
    return hashlib.sha256(seed.encode()).hexdigest()


def mint_offline_token(
    subject: str,
    claims: Optional[Dict[str, Any]] = None,
    ttl_s: int = 3600,
    audience: str = "garden",
) -> FederatedCredential:
    secret = resolve_offline_secret()
    now = int(time.time())
    payload = {
        "sub": subject,
        "iss": "garden://offline",
        "aud": audience,
        "iat": now,
        "exp": now + int(ttl_s),
        "claims": claims or {},
        "provider": CloudProvider.OFFLINE.value,
    }
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    sig = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    token = f"{body}.{sig}"
    oc = OIDCClaims(
        sub=subject,
        iss="garden://offline",
        aud=audience,
        exp=now + int(ttl_s),
        iat=now,
        provider=CloudProvider.OFFLINE.value,
        raw=payload,
        verified=True,
    )
    return FederatedCredential(
        provider=CloudProvider.OFFLINE.value,
        access_token=token,
        expires_in=int(ttl_s),
        expires_at=float(now + int(ttl_s)),
        claims=oc,
        meta={"secret_len": len(secret), "sig_len": len(sig)},
    )


def verify_offline_token(token: str) -> OIDCClaims:
    """
    Verify an offline token minted by mint_offline_token().
    """
    secret = resolve_offline_secret()
    try:
        body, sig = token.rsplit(".", 1)
    except ValueError as e:
        raise ValueError("malformed offline token") from e
    expect = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expect):
        raise ValueError("bad offline signature")
    payload = json.loads(body)
    if int(time.time()) > int(payload.get("exp", 0)):
        raise ValueError("offline token expired")
    return OIDCClaims(
        sub=str(payload.get("sub", "")),
        iss=str(payload.get("iss", "")),
        aud=payload.get("aud"),
        exp=int(payload.get("exp", 0)),
        iat=int(payload.get("iat", 0)),
        provider=CloudProvider.OFFLINE.value,
        raw=payload,
        verified=True,
    )


def fetch_github_actions_id_token(audience: Optional[str] = None) -> str:
    url = _env("ACTIONS_ID_TOKEN_REQUEST_URL")
    req_token = _env("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
    if not url or not req_token:
        raise RuntimeError(
            "Not in GitHub Actions OIDC context "
            "(ACTIONS_ID_TOKEN_REQUEST_URL / TOKEN missing). "
            "Set permissions: id-token: write"
        )
    aud = audience or _env("OIDC_AUDIENCE", "sts.amazonaws.com")
    full = f"{url}&audience={urllib.parse.quote(aud)}" if "audience=" not in url else url
    status, body = _http_json(full, headers={"Authorization": f"Bearer {req_token}"})
    if status != 200 or not body.get("value"):
        raise RuntimeError(f"GitHub ID token request failed: {status} {body}")
    return str(body["value"])


def aws_assume_role_with_web_identity(
    role_arn: Optional[str] = None,
    web_identity_token: Optional[str] = None,
    session_name: str = "garden-oidc",
    region: Optional[str] = None,
    duration_seconds: int = 3600,
) -> FederatedCredential:
    role_arn = role_arn or _env("AWS_ROLE_ARN")
    if not role_arn:
        raise RuntimeError("AWS_ROLE_ARN required")
    token = web_identity_token
    if not token:
        token_file = _env("AWS_WEB_IDENTITY_TOKEN_FILE")
        if token_file and Path(token_file).exists():
            token = Path(token_file).read_text(encoding="utf-8").strip()
        else:
            token = fetch_github_actions_id_token(audience="sts.amazonaws.com")
    region = region or _env("AWS_REGION", _env("AWS_DEFAULT_REGION", "us-east-1"))
    params = urllib.parse.urlencode(
        {
            "Action": "AssumeRoleWithWebIdentity",
            "Version": "2011-06-15",
            "RoleArn": role_arn,
            "RoleSessionName": session_name,
            "WebIdentityToken": token,
            "DurationSeconds": str(duration_seconds),
        }
    )
    url = f"https://sts.{region}.amazonaws.com/?{params}"
    status, body = _http_json(url, method="GET", headers={"Accept": "application/json"})
    if status != 200:
        raise RuntimeError(f"STS AssumeRoleWithWebIdentity failed status={status} body={body}")
    creds = (
        body.get("AssumeRoleWithWebIdentityResponse", {})
        .get("AssumeRoleWithWebIdentityResult", {})
        .get("Credentials", {})
    )
    if not creds and body.get("Credentials"):
        creds = body["Credentials"]
    packed = json.dumps(
        {
            "AccessKeyId": creds.get("AccessKeyId") or body.get("AccessKeyId", ""),
            "SecretAccessKey": creds.get("SecretAccessKey") or body.get("SecretAccessKey", ""),
            "SessionToken": creds.get("SessionToken") or body.get("SessionToken", ""),
            "Region": region,
        },
        separators=(",", ":"),
    )
    claims = None
    try:
        pl = decode_jwt_unverified(token)["payload"]
        claims = OIDCClaims(
            sub=str(pl.get("sub", "")),
            iss=str(pl.get("iss", "")),
            aud=pl.get("aud"),
            exp=int(pl.get("exp", 0)),
            iat=int(pl.get("iat", 0)),
            provider=CloudProvider.AWS.value,
            raw=pl,
            verified=False,
        )
    except Exception:
        pass
    return FederatedCredential(
        provider=CloudProvider.AWS.value,
        access_token=packed,
        expires_in=duration_seconds,
        expires_at=time.time() + duration_seconds,
        claims=claims,
        meta={"role_arn": role_arn, "region": region},
    )


def gcp_federate(
    workload_provider: Optional[str] = None,
    service_account: Optional[str] = None,
    id_token: Optional[str] = None,
    audience: Optional[str] = None,
) -> FederatedCredential:
    provider = workload_provider or _env("GCP_WORKLOAD_PROVIDER")
    sa = service_account or _env("GCP_SERVICE_ACCOUNT")
    if not provider:
        raise RuntimeError("GCP_WORKLOAD_PROVIDER required")
    token = id_token or fetch_github_actions_id_token(
        audience=audience or f"https://iam.googleapis.com/{provider}"
    )
    sts_body = json.dumps(
        {
            "audience": f"//iam.googleapis.com/{provider}",
            "grantType": "urn:ietf:params:oauth:grant-type:token-exchange",
            "requestedTokenType": "urn:ietf:params:oauth:token-type:access_token",
            "scope": "https://www.googleapis.com/auth/cloud-platform",
            "subjectTokenType": "urn:ietf:params:oauth:token-type:jwt",
            "subjectToken": token,
        }
    ).encode("utf-8")
    status, sts = _http_json(
        "https://sts.googleapis.com/v1/token",
        method="POST",
        headers={"Content-Type": "application/json"},
        body=sts_body,
    )
    if status != 200 or not sts.get("access_token"):
        raise RuntimeError(f"GCP STS exchange failed: {status} {sts}")
    federated = sts["access_token"]
    final_token = federated
    expires_in = int(sts.get("expires_in", 3600))
    if sa:
        gen_body = json.dumps(
            {"scope": ["https://www.googleapis.com/auth/cloud-platform"], "lifetime": f"{min(expires_in, 3600)}s"}
        ).encode("utf-8")
        g_status, g_body = _http_json(
            f"https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{sa}:generateAccessToken",
            method="POST",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {federated}"},
            body=gen_body,
        )
        if g_status != 200 or not g_body.get("accessToken"):
            raise RuntimeError(f"GCP generateAccessToken failed: {g_status} {g_body}")
        final_token = g_body["accessToken"]
    return FederatedCredential(
        provider=CloudProvider.GCP.value,
        access_token=final_token,
        expires_in=expires_in,
        expires_at=time.time() + expires_in,
        meta={"workload_provider": provider, "service_account": sa or None},
    )


def azure_federate(
    tenant_id: Optional[str] = None,
    client_id: Optional[str] = None,
    federated_token: Optional[str] = None,
    scope: str = "https://management.azure.com/.default",
) -> FederatedCredential:
    tenant = tenant_id or _env("AZURE_TENANT_ID")
    client = client_id or _env("AZURE_CLIENT_ID")
    if not tenant or not client:
        raise RuntimeError("AZURE_TENANT_ID and AZURE_CLIENT_ID required")
    token = federated_token
    if not token:
        path = _env("AZURE_FEDERATED_TOKEN_FILE")
        if path and Path(path).exists():
            token = Path(path).read_text(encoding="utf-8").strip()
        else:
            token = fetch_github_actions_id_token(audience="api://AzureADTokenExchange")
    form = urllib.parse.urlencode(
        {
            "grant_type": "client_credentials",
            "client_id": client,
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
            "client_assertion": token,
            "scope": scope,
        }
    ).encode("utf-8")
    status, body = _http_json(
        f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        body=form,
    )
    if status != 200 or not body.get("access_token"):
        raise RuntimeError(f"Azure token exchange failed: {status} {body}")
    expires_in = int(body.get("expires_in", 3600))
    return FederatedCredential(
        provider=CloudProvider.AZURE.value,
        access_token=str(body["access_token"]),
        token_type=str(body.get("token_type", "Bearer")),
        expires_in=expires_in,
        expires_at=time.time() + expires_in,
        meta={"tenant_id": tenant, "client_id": client, "scope": scope},
    )


class OIDCCloudClient:
    """Unified entry for cloud-provider OIDC federation."""

    def __init__(self, prefer_offline: Optional[bool] = None):
        self.prefer_offline = offline_mode() if prefer_offline is None else prefer_offline
        self._cache: Dict[str, FederatedCredential] = {}

    def status(self) -> Dict[str, Any]:
        return {
            "entry": ENTRY,
            "seal": SEAL,
            "offline_mode": self.prefer_offline,
            "crypto_available": CRYPTO_AVAILABLE,
            "github_actions": bool(_env("ACTIONS_ID_TOKEN_REQUEST_URL")),
            "aws_role_configured": bool(_env("AWS_ROLE_ARN")),
            "gcp_provider_configured": bool(_env("GCP_WORKLOAD_PROVIDER")),
            "azure_configured": bool(_env("AZURE_TENANT_ID") and _env("AZURE_CLIENT_ID")),
            "issuer": _env("OIDC_ISSUER") or None,
            "cached_providers": list(self._cache.keys()),
        }

    def get_id_token(self, audience: Optional[str] = None) -> str:
        if self.prefer_offline:
            return mint_offline_token("garden-agent", audience=audience or "garden").access_token
        if _env("ACTIONS_ID_TOKEN_REQUEST_URL"):
            return fetch_github_actions_id_token(audience)
        raise RuntimeError("No ID token source (not in GHA and OIDC_OFFLINE not set)")

    def federate(self, provider: str, **kwargs: Any) -> FederatedCredential:
        p = provider.lower().strip()
        if self.prefer_offline or p == CloudProvider.OFFLINE.value:
            cred = mint_offline_token(
                kwargs.get("subject", "garden-agent"),
                claims=kwargs.get("claims"),
                ttl_s=kwargs.get("ttl_s", 3600),
                audience=kwargs.get("audience", "garden"),
            )
            self._cache[CloudProvider.OFFLINE.value] = cred
            return cred
        if p == CloudProvider.GITHUB.value:
            token = fetch_github_actions_id_token(kwargs.get("audience"))
            decoded = decode_jwt_unverified(token)
            pl = decoded["payload"]
            claims = OIDCClaims(
                sub=str(pl.get("sub", "")),
                iss=str(pl.get("iss", "")),
                aud=pl.get("aud"),
                exp=int(pl.get("exp", 0)),
                iat=int(pl.get("iat", 0)),
                provider=CloudProvider.GITHUB.value,
                raw=pl,
                verified=False,
            )
            cred = FederatedCredential(
                provider=CloudProvider.GITHUB.value,
                access_token=token,
                expires_in=max(0, claims.exp - int(time.time())),
                expires_at=float(claims.exp),
                claims=claims,
            )
            self._cache[p] = cred
            return cred
        if p == CloudProvider.AWS.value:
            cred = aws_assume_role_with_web_identity(
                **{k: v for k, v in kwargs.items() if k in {
                    "role_arn", "web_identity_token", "session_name", "region", "duration_seconds"
                }}
            )
            self._cache[p] = cred
            return cred
        if p == CloudProvider.GCP.value:
            cred = gcp_federate(
                **{k: v for k, v in kwargs.items() if k in {
                    "workload_provider", "service_account", "id_token", "audience"
                }}
            )
            self._cache[p] = cred
            return cred
        if p == CloudProvider.AZURE.value:
            cred = azure_federate(
                **{k: v for k, v in kwargs.items() if k in {
                    "tenant_id", "client_id", "federated_token", "scope"
                }}
            )
            self._cache[p] = cred
            return cred
        if p == CloudProvider.GENERIC.value:
            token = kwargs.get("token") or self.get_id_token(kwargs.get("audience"))
            issuer = kwargs.get("issuer") or _env("OIDC_ISSUER")
            jwks = None
            if issuer:
                try:
                    jwks = fetch_jwks(discover_jwks_uri(issuer))
                except Exception as e:
                    LOG.warning("JWKS discover failed: %s", e)
            claims = verify_jwt(
                token,
                issuer=issuer or None,
                audience=kwargs.get("audience") or _env("OIDC_AUDIENCE") or None,
                jwks=jwks,
            )
            claims.provider = CloudProvider.GENERIC.value
            cred = FederatedCredential(
                provider=CloudProvider.GENERIC.value,
                access_token=token,
                expires_in=max(0, claims.exp - int(time.time())),
                expires_at=float(claims.exp),
                claims=claims,
            )
            self._cache[p] = cred
            return cred
        raise ValueError(f"unknown provider: {provider}")

    def refresh_jwks(self, issuer: Optional[str] = None) -> Dict[str, Any]:
        iss = issuer or _env("OIDC_ISSUER")
        if not iss:
            raise RuntimeError("OIDC_ISSUER required to refresh JWKS")
        return fetch_jwks(discover_jwks_uri(iss))


# ─── CLI ──────────────────────────────────────────────────────────────
def main(argv: Optional[List[str]] = None) -> int:
    import argparse

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="OIDC cloud provider federation")
    parser.add_argument(
        "command",
        choices=["status", "federate", "mint-offline", "verify-offline", "refresh-jwks"],
        nargs="?",
        default="status",
    )
    parser.add_argument("--provider", choices=[p.value for p in CloudProvider], default="offline")
    parser.add_argument("--subject", default="garden-agent")
    parser.add_argument("--audience", default=None)
    parser.add_argument("--token", default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args(argv)

    client = OIDCCloudClient(prefer_offline=True if args.offline else None)

    if args.command == "status":
        out: Any = client.status()
    elif args.command == "mint-offline":
        cred = mint_offline_token(args.subject, audience=args.audience or "garden")
        out = cred.to_dict()
        out["access_token"] = cred.access_token
    elif args.command == "verify-offline":
        if not args.token:
            print("error: --token required", flush=True)
            return 2
        out = verify_offline_token(args.token).to_dict()
    elif args.command == "refresh-jwks":
        out = client.refresh_jwks()
    else:
        try:
            cred = client.federate(args.provider, subject=args.subject, audience=args.audience)
            out = cred.to_dict()
        except Exception as e:
            out = {"error": str(e), "provider": args.provider, "seal": SEAL}
            print(json.dumps(out, indent=2) if args.json else f"ERROR: {e}")
            return 1

    if args.json:
        print(json.dumps(out, indent=2, default=str))
    else:
        print(f"🜁∀ OIDC CLOUD — Entry {ENTRY}")
        print("=" * 50)
        print(json.dumps(out, indent=2, default=str))
        print(SEAL)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
