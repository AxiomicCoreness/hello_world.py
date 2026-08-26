"""
MCP Connector Client — OAuth 2.0 endpoints client.
Uses MCP_CONNECTOR_URL (default local Port 380). No GARDEN_SECRETS env name.
Never logs client secrets or tokens.
Seal: ∀∞φ² · MCP_CONNECTOR · WOOD_DRAGON_0.91 · SEALED
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests

BASE_URL = os.getenv("MCP_CONNECTOR_URL", "http://127.0.0.1:380")
TIMEOUT = float(os.getenv("MCP_CONNECTOR_TIMEOUT", "5.0"))
MAX_RETRIES = int(os.getenv("MCP_CONNECTOR_RETRIES", "3"))

_DEFAULT_ENDPOINTS = {
    "token": "/oauth/token",
    "authorize": "/oauth/authorize",
    "introspect": "/oauth/introspect",
    "revoke": "/oauth/revoke",
    "health": "/health",
    "sign": "/oauth/sign",
}


def _load_endpoints() -> Dict[str, str]:
    raw = os.getenv("MCP_CONNECTOR_ENDPOINTS", "")
    if not raw.strip():
        return dict(_DEFAULT_ENDPOINTS)
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            merged = dict(_DEFAULT_ENDPOINTS)
            merged.update({str(k): str(v) for k, v in parsed.items()})
            return merged
    except (ValueError, TypeError):
        pass
    return dict(_DEFAULT_ENDPOINTS)


ENDPOINTS = _load_endpoints()


def _url(path: str, base_url: Optional[str] = None) -> str:
    return urljoin((base_url or BASE_URL).rstrip("/") + "/", path.lstrip("/"))


def _request(
    method: str,
    path: str,
    *,
    base_url: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    url = _url(path, base_url=base_url)
    kwargs.setdefault("timeout", TIMEOUT)
    last_error: Optional[BaseException] = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.request(method, url, **kwargs)
            resp.raise_for_status()
            if not resp.content:
                return {}
            try:
                data = resp.json()
            except ValueError as e:
                raise RuntimeError(f"MCP connector invalid JSON from {path}") from e
            return data if isinstance(data, dict) else {"data": data}
        except (requests.RequestException, ValueError) as e:
            last_error = e
            if attempt == MAX_RETRIES - 1:
                raise RuntimeError(f"MCP connector error: {e}") from e
    raise RuntimeError(f"MCP connector error: {last_error}")


def get_token(client_id: str, client_secret: str, scope: str = "") -> Dict[str, Any]:
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": scope,
    }
    return _request("POST", ENDPOINTS["token"], data=data)


def introspect_token(token: str) -> Dict[str, Any]:
    return _request("POST", ENDPOINTS["introspect"], data={"token": token})


def revoke_token(token: str) -> bool:
    resp = _request("POST", ENDPOINTS["revoke"], data={"token": token})
    return bool(resp.get("revoked", False))

def health_check() -> bool:
    try:
        resp = _request("GET", ENDPOINTS["health"])
        return resp.get("status") == "ok"
    except RuntimeError:
        return False


def sign_payload(payload: Dict[str, Any], token: str) -> Dict[str, Any]:
    headers = {"Authorization": f"Bearer {token}"}
    return _request("POST", ENDPOINTS["sign"], json=payload, headers=headers)


class MCPConnector:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or BASE_URL
        self.token: Optional[str] = None

    def authenticate(self, client_id: str, client_secret: str, scope: str = "") -> bool:
        try:
            resp = get_token(client_id, client_secret, scope)
            self.token = resp.get("access_token")
            return bool(self.token)
        except RuntimeError:
            return False

    def introspect(self) -> Optional[Dict[str, Any]]:
        if not self.token:
            return None
        return introspect_token(self.token)

    def sign(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.token:
            return None
        return sign_payload(payload, self.token)

    def health(self) -> bool:
        return health_check()
