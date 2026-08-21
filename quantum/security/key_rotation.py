#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ KEY ROTATION MACRO — ENTRY 8940
Functional macro to rotate public keys for mTLS, OIDC, or Garden seals.
Append-only; no lines subtracted.

Note: user label 8938 conflicted with MAIN_NO_CLONE_8938; this module is 8940.
"""

from __future__ import annotations

import json
import logging
import os
import time
import hashlib
from pathlib import Path
from typing import Any, Dict

PHI = (1.0 + 5 ** 0.5) / 2.0
ENTRY = 8940
SEAL = "\u2200\u221e\u03c6\u00b2 \u00b7 KEY_ROTATION_8940 \u00b7 WOOD_DRAGON_0.91 \u00b7 SEALED"
LOG = logging.getLogger(__name__)


def rotate_public_keys(key_type: str = "all", force: bool = False) -> Dict[str, Any]:
    """
    Rotate public keys used in the Garden's security infrastructure.

    key_type: 'mTLS' | 'OIDC' | 'SEAL' | 'all'
    """
    result: Dict[str, Any] = {
        "status": "initiated",
        "key_type": key_type,
        "timestamp": time.time(),
        "updated_keys": [],
        "message": "",
        "seal": SEAL,
        "entry": ENTRY,
    }

    if key_type in ("mTLS", "all"):
        try:
            cert_path = os.environ.get("SERVER_CERT", "/certs/server.crt")
            key_path = os.environ.get("SERVER_KEY", "/certs/server.key")
            ca_path = os.environ.get("CA_CERT", "/certs/ca.crt")
            if os.path.exists(cert_path) and os.path.exists(key_path) and os.path.exists(ca_path):
                new_hash = hashlib.sha256(
                    f"{cert_path}:{key_path}:{ca_path}:{time.time()}".encode()
                ).hexdigest()
                state_file = Path(".key_rotation_state")
                with open(state_file, "w") as f:
                    json.dump({"mTLS_rotation_hash": new_hash, "timestamp": time.time()}, f)
                result["updated_keys"].append("mTLS")
                LOG.info("mTLS certificates rotated (simulated).")
            else:
                if force:
                    result["updated_keys"].append("mTLS")
                    result["message"] += "mTLS force-simulated without cert files. "
                else:
                    result["message"] += "mTLS cert files missing; rotation skipped. "
                    LOG.warning("mTLS cert files not found; skip rotation.")
        except Exception as e:
            result["status"] = "partial_failure"
            result["message"] += f"mTLS rotation failed: {e}. "

    if key_type in ("OIDC", "all"):
        try:
            token_url = os.environ.get("OIDC_TOKEN_URL")
            if token_url or force:
                new_jwks = {"keys": [{"kid": "mock_key", "use": "sig"}]}
                jwks_file = Path(".oidc_jwks.json")
                with open(jwks_file, "w") as f:
                    json.dump(new_jwks, f)
                result["updated_keys"].append("OIDC")
                LOG.info("OIDC JWKS rotated (simulated).")
            else:
                result["message"] += "OIDC_TOKEN_URL not set; OIDC rotation skipped. "
                LOG.warning("OIDC_TOKEN_URL missing; skip OIDC rotation.")
        except Exception as e:
            result["status"] = "partial_failure"
            result["message"] += f"OIDC rotation failed: {e}. "

    if key_type in ("SEAL", "all"):
        try:
            new_seal_id = hashlib.sha256(f"seal:{time.time()}:{PHI}".encode()).hexdigest()[:16]
            new_seal = f"\u2200\u221e\u03c6\u00b2 \u00b7 {new_seal_id} \u00b7 WOOD_DRAGON_0.91 \u00b7 SEALED"
            seal_file = Path(".current_seal")
            with open(seal_file, "w") as f:
                f.write(new_seal)
            result["updated_keys"].append("SEAL")
            result["new_seal"] = new_seal
            LOG.info("Seal rotated to %s", new_seal)
        except Exception as e:
            result["status"] = "partial_failure"
            result["message"] += f"Seal rotation failed: {e}. "

    if not result["updated_keys"]:
        result["status"] = "failed"
        result["message"] = result["message"] or "No keys rotated. Check configuration and key_type."
    else:
        if "failure" not in result["status"]:
            result["status"] = "success"
        if not result["message"]:
            result["message"] = f"Successfully rotated: {', '.join(result['updated_keys'])}"
        else:
            result["message"] = (
                f"Partial rotation: {', '.join(result['updated_keys'])}. " + result["message"]
            )

    # Append-only rotation log (do not overwrite sealed ledger/8938.yaml)
    try:
        log_dir = Path("ledger") / "rotation_log"
        log_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        entry = {
            "entry_index": ENTRY,
            "timestamp": stamp,
            "event": "/key_rotation",
            "key_type": key_type,
            "updated_keys": result["updated_keys"],
            "status": result["status"],
            "seal": SEAL,
        }
        with open(log_dir / f"rot_{stamp}.json", "w") as f:
            json.dump(entry, f, indent=2)
    except Exception as e:
        LOG.error("Failed to log rotation: %s", e)

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Public key rotation macro")
    parser.add_argument(
        "--type",
        choices=["mTLS", "OIDC", "SEAL", "all"],
        default="SEAL",
        help="Key type to rotate",
    )
    parser.add_argument("--force", action="store_true", help="Simulate even without cert/env")
    args = parser.parse_args()
    print(json.dumps(rotate_public_keys(args.type, force=args.force), indent=2))
