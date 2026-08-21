#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ JWKS CACHE — ENTRY 8945

Read-through JWKS cache with per-issuer memory + disk, TTL / Cache-Control,
refresh on unknown kid, rate-limited refetch, stale-while-error.

Seal: ∀∞φ² · JWKS_CACHE_8945 · WOOD_DRAGON_0.91 · SEALED
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI_SQ = PHI * PHI
ENTRY = 8945
SEAL = "\u2200\u221e\u03c6\u00b2 \u00b7 JWKS_CACHE_8945 \u00b7 WOOD_DRAGON_0.91 \u00b7 SEALED"
LOG = logging.getLogger("jwks_cache")

DEFAULT_TTL = 600.0 * PHI_INV
MIN_REFRESH_INTERVAL = 300.0 * (PHI_INV ** 2)
STALE_MULTIPLIER = PHI_SQ


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def _issuer_key(issuer: str) -> str:
    return hashlib.sha256(issuer.encode("utf-8")).hexdigest()[:32]


@dataclass
class CacheEntry:
    issuer: str
    jwks: Dict[str, Any]
    fetched_at: float
    expires_at: float
    etag: Optional[str] = None
    jwks_uri: Optional[str] = None

    def is_fresh(self, now: Optional[float] = None) -> bool:
        now = now if now is not None else time.time()
        return now < self.expires_at

    def is_stale_usable(self, now: Optional[float] = None, ttl: float = DEFAULT_TTL) -> bool:
        now = now if now is not None else time.time()
        return now < self.fetched_at + ttl * STALE_MULTIPLIER

    def has_kid(self, kid: str) -> bool:
        return any(k.get("kid") == kid for k in (self.jwks.get("keys") or []))

    def get_jwk(self, kid: Optional[str] = None) -> Optional[Dict[str, Any]]:
        keys = self.jwks.get("keys") or []
        if not keys:
            return None
        if kid:
            for k in keys:
                if k.get("kid") == kid:
                    return k
            return None
        return keys[0]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class JwksCache:
    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        ttl: float = DEFAULT_TTL,
        min_refresh_interval: float = MIN_REFRESH_INTERVAL,
    ):
        self.cache_dir = cache_dir or Path(_env("OIDC_JWKS_CACHE_DIR", ".oidc_jwks_cache"))
        self.ttl = float(_env("OIDC_JWKS_TTL", str(ttl)) or ttl)
        self.min_refresh_interval = min_refresh_interval
        self._mem: Dict[str, CacheEntry] = {}
        self._last_fetch_attempt: Dict[str, float] = {}
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _disk_path(self, issuer: str) -> Path:
        return self.cache_dir / f"{_issuer_key(issuer)}.json"

    def _load_disk(self, issuer: str) -> Optional[CacheEntry]:
        path = self._disk_path(issuer)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return CacheEntry(
                issuer=data.get("issuer", issuer),
                jwks=data.get("jwks") or {"keys": []},
                fetched_at=float(data.get("fetched_at", 0)),
                expires_at=float(data.get("expires_at", 0)),
                etag=data.get("etag"),
                jwks_uri=data.get("jwks_uri"),
            )
        except Exception as e:
            LOG.warning("disk load failed for %s: %s", issuer, e)
            return None

    def _save_disk(self, entry: CacheEntry) -> None:
        path = self._disk_path(entry.issuer)
        try:
            path.write_text(json.dumps(entry.to_dict(), indent=2), encoding="utf-8")
            legacy = Path(_env("OIDC_JWKS_CACHE", ".oidc_jwks.json"))
            legacy.write_text(
                json.dumps(
                    {
                        **entry.jwks,
                        "_garden_meta": {
                            "issuer": entry.issuer,
                            "fetched_at": entry.fetched_at,
                            "expires_at": entry.expires_at,
                            "jwks_uri": entry.jwks_uri,
                            "entry": ENTRY,
                            "seal": SEAL,
                        },
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception as e:
            LOG.warning("disk save failed: %s", e)

    def _http_get(self, url: str, etag: Optional[str] = None) -> Tuple[int, Dict[str, Any], Dict[str, str]]:
        headers = {"Accept": "application/json"}
        if etag:
            headers["If-None-Match"] = etag
        req = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=15.0) as resp:
                raw = resp.read().decode("utf-8")
                body = json.loads(raw) if raw else {}
                hdrs = {k.lower(): v for k, v in resp.headers.items()}
                return resp.status, body, hdrs
        except urllib.error.HTTPError as e:
            if e.code == 304:
                return 304, {}, {k.lower(): v for k, v in e.headers.items()}
            raw = e.read().decode("utf-8", errors="replace")
            try:
                body = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                body = {"error": raw}
            return e.code, body, {}
        except Exception as e:
            return 0, {"error": str(e)}, {}

    def discover_jwks_uri(self, issuer: str) -> str:
        issuer = issuer.rstrip("/")
        status, doc, _ = self._http_get(f"{issuer}/.well-known/openid-configuration")
        if status == 200 and doc.get("jwks_uri"):
            return str(doc["jwks_uri"])
        if "token.actions.githubusercontent.com" in issuer:
            return "https://token.actions.githubusercontent.com/.well-known/jwks"
        raise RuntimeError(f"jwks_uri discovery failed issuer={issuer} status={status}")

    def _parse_max_age(self, headers: Dict[str, str], fallback: float) -> float:
        cc = headers.get("cache-control", "")
        for part in cc.split(","):
            part = part.strip().lower()
            if part.startswith("max-age="):
                try:
                    return float(part.split("=", 1)[1])
                except ValueError:
                    pass
            if part in ("no-cache", "no-store"):
                return min(fallback, 60.0)
        return fallback

    def _rate_limited(self, issuer: str, now: float) -> bool:
        last = self._last_fetch_attempt.get(issuer, 0.0)
        return (now - last) < self.min_refresh_interval

    def fetch(self, issuer: str, jwks_uri: Optional[str] = None, force: bool = False) -> CacheEntry:
        now = time.time()
        if not force and self._rate_limited(issuer, now):
            existing = self._mem.get(issuer) or self._load_disk(issuer)
            if existing and existing.is_stale_usable(now, self.ttl):
                self._mem[issuer] = existing
                return existing
            raise RuntimeError(f"JWKS refetch rate-limited for issuer={issuer}")

        self._last_fetch_attempt[issuer] = now
        uri = jwks_uri or self.discover_jwks_uri(issuer)
        prev = self._mem.get(issuer) or self._load_disk(issuer)
        status, body, headers = self._http_get(uri, etag=prev.etag if prev else None)

        if status == 304 and prev:
            prev.fetched_at = now
            prev.expires_at = now + self._parse_max_age(headers, self.ttl)
            self._mem[issuer] = prev
            self._save_disk(prev)
            return prev

        if status != 200 or "keys" not in body:
            if prev and prev.is_stale_usable(now, self.ttl):
                LOG.warning("JWKS fetch failed status=%s; serving stale", status)
                self._mem[issuer] = prev
                return prev
            raise RuntimeError(f"JWKS fetch failed status={status} body={body}")

        ttl = self._parse_max_age(headers, self.ttl)
        entry = CacheEntry(
            issuer=issuer,
            jwks=body,
            fetched_at=now,
            expires_at=now + ttl,
            etag=headers.get("etag"),
            jwks_uri=uri,
        )
        self._mem[issuer] = entry
        self._save_disk(entry)
        return entry

    def get(
        self,
        issuer: str,
        kid: Optional[str] = None,
        jwks_uri: Optional[str] = None,
    ) -> CacheEntry:
        now = time.time()
        entry = self._mem.get(issuer)
        if entry is None:
            entry = self._load_disk(issuer)
            if entry:
                self._mem[issuer] = entry

        need_fetch = entry is None or not entry.is_fresh(now)
        if entry and kid and not entry.has_kid(kid):
            need_fetch = True

        if need_fetch:
            try:
                entry = self.fetch(
                    issuer,
                    jwks_uri=jwks_uri,
                    force=bool(kid and entry and not entry.has_kid(kid)),
                )
            except Exception as e:
                if entry and entry.is_stale_usable(now, self.ttl):
                    LOG.warning("fetch failed (%s); using stale", e)
                else:
                    raise
        assert entry is not None
        return entry

    def get_jwk(self, issuer: str, kid: Optional[str] = None) -> Dict[str, Any]:
        entry = self.get(issuer, kid=kid)
        jwk = entry.get_jwk(kid)
        if jwk is None:
            raise KeyError(f"kid={kid} not in JWKS for issuer={issuer}")
        return jwk

    def invalidate(self, issuer: str) -> None:
        self._mem.pop(issuer, None)
        path = self._disk_path(issuer)
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass

    def status(self) -> Dict[str, Any]:
        return {
            "entry": ENTRY,
            "seal": SEAL,
            "ttl": self.ttl,
            "min_refresh_interval": self.min_refresh_interval,
            "stale_multiplier": STALE_MULTIPLIER,
            "memory_issuers": list(self._mem.keys()),
            "cache_dir": str(self.cache_dir),
        }


_CACHE: Optional[JwksCache] = None


def get_jwks_cache() -> JwksCache:
    global _CACHE
    if _CACHE is None:
        _CACHE = JwksCache()
    return _CACHE
