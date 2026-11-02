# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Per-device bearer tokens for the v3t ``/llm`` route — only sha256 hashes are stored.

Admin CLI (never prints a token; a minted token goes only into a new mode-600 file)::

    python -I src/device_tokens.py --db DB mint  <device> --out /path/token.txt
    python -I src/device_tokens.py --db DB revoke <device>
    python -I src/device_tokens.py --db DB list

Single-user: normally exactly one live token, ``owner``, used by both the
iPhone and the TeaVM browser page (rotate = mint again; revoke = revoke owner).
Device names: ``[A-Za-z0-9_.-]{1,64}``. Minting a device that already has a live
token revokes the old one first (one live token per device).
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

DEVICE_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
PREFIX = "cyt_"

_SQL = (
    """CREATE TABLE IF NOT EXISTS v3t_device_tokens (
        id           INTEGER PRIMARY KEY,
        device       TEXT NOT NULL,
        token_sha256 TEXT NOT NULL UNIQUE,
        created_at   TEXT NOT NULL,
        revoked_at   TEXT NULL
    )""",
    "CREATE UNIQUE INDEX IF NOT EXISTS v3t_device_one_live ON v3t_device_tokens(device)"
    " WHERE revoked_at IS NULL",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class TokenStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        con = self._con()
        try:
            with con:
                for stmt in _SQL:
                    con.execute(stmt)
        finally:
            con.close()

    def _con(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self.path), timeout=5)
        con.execute("PRAGMA busy_timeout = 5000")
        return con

    def mint(self, device: str) -> str:
        if not DEVICE_RE.match(device or ""):
            raise ValueError("device must match [A-Za-z0-9_.-]{1,64}")
        token = PREFIX + secrets.token_urlsafe(32)
        con = self._con()
        try:
            with con:
                con.execute("UPDATE v3t_device_tokens SET revoked_at = ? WHERE device = ? AND revoked_at IS NULL",
                            (_now(), device))
                con.execute("INSERT INTO v3t_device_tokens (device, token_sha256, created_at) VALUES (?, ?, ?)",
                            (device, token_hash(token), _now()))
        finally:
            con.close()
        return token

    def revoke(self, device: str) -> int:
        con = self._con()
        try:
            with con:
                return con.execute("UPDATE v3t_device_tokens SET revoked_at = ? WHERE device = ?"
                                   " AND revoked_at IS NULL", (_now(), device)).rowcount
        finally:
            con.close()

    def verify(self, token: str) -> Optional[str]:
        """→ device name for a live token, else None. Constant-time compare on the hash."""
        if not token or not token.startswith(PREFIX) or len(token) > 200:
            return None
        h = token_hash(token)
        con = self._con()
        try:
            row = con.execute("SELECT device, token_sha256 FROM v3t_device_tokens"
                              " WHERE token_sha256 = ? AND revoked_at IS NULL", (h,)).fetchone()
        finally:
            con.close()
        if row and hmac.compare_digest(row[1], h):
            return row[0]
        return None

    def list(self) -> List[Dict[str, Optional[str]]]:
        con = self._con()
        try:
            rows = con.execute("SELECT device, created_at, revoked_at FROM v3t_device_tokens ORDER BY id").fetchall()
        finally:
            con.close()
        return [{"device": d, "created_at": c, "revoked_at": r} for d, c, r in rows]


def write_secret(path: Path, token: str) -> None:
    """Write ``token`` to a NEW file created mode 600 (refuses to overwrite)."""
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(token + "\n")
    os.chmod(path, 0o600)


def main(argv: Optional[List[str]] = None) -> int:
    try:
        from .v3t_route import DEFAULT_DB, V3tStore
    except ImportError:  # pragma: no cover
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from src.v3t_route import DEFAULT_DB, V3tStore  # type: ignore
    ap = argparse.ArgumentParser(description="v3t device token admin (prints no tokens)")
    ap.add_argument("--db", default=os.environ.get("V3T_DB", str(DEFAULT_DB)))
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("mint")
    m.add_argument("device")
    m.add_argument("--out", required=True, help="new file to receive the token (mode 600)")
    r = sub.add_parser("revoke")
    r.add_argument("device")
    sub.add_parser("list")
    a = ap.parse_args(argv)
    store = V3tStore(Path(a.db)).tokens
    if a.cmd == "mint":
        out = Path(a.out)
        if out.exists():
            print(f"refusing: {out} exists", file=sys.stderr)
            return 2
        write_secret(out, store.mint(a.device))
        print(f"minted token for device={a.device} -> {out} (mode 600; value not printed)")
    elif a.cmd == "revoke":
        print(f"revoked {store.revoke(a.device)} live token(s) for device={a.device}")
    else:
        for row in store.list():
            print(f"{row['device']}\tcreated={row['created_at']}\trevoked={row['revoked_at'] or '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
