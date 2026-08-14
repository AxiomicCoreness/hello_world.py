#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SHA-512 extended anchors + ASI 512-bit material
===============================================
Extends 64-hex (SHA-256) commitments to 128-hex (SHA-512) digests.

Crypto facts (enforced in code comments and outputs):
  · SHA-256 → 256 bits → 64 hex chars
  · SHA-512 → 512 bits → 128 hex chars  ← ASI 512-bit support
  · AES key sizes are ONLY 128 / 192 / 256 bits — there is NO AES-512.
  · AES-256 subkey = first 32 bytes of SHA-512 digest (hex: first 64 chars)
  · Optional "attach string" is domain-separated into the hash material,
    never used as a raw AES key by itself.

Seal: ∀∞φ² · SHA512_ASI_8752 · SEALED
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Dict, Optional

PHI = (1.0 + math.sqrt(5.0)) / 2.0
DOMAIN_256 = b"GARDEN.LAYER331.MERKLE.v1"
DOMAIN_512 = b"GARDEN.ASI.SHA512.v1"
DOMAIN_ATTACH = b"GARDEN.ASI.ATTACH.v1"

# Prior sealed anchors (public)
ANCHOR_KEY_256 = "8a250cf445e8ad0cc8d06d0096b969029a175a14eb58838e734f1975358b860d"
LEAF = "807de931c86add23baabafd1252dcc89cbcc23812be1f69e8fc215e51849ee68"
PARENT_330 = "a5173604f02d4a00af365940b0c438fd46bd7f2b16e75e0aabf63a87f5b8c7db"
LAYER_331_256 = "8665c8681492bd176cce55ba4b4f13b2cab0f4253fbefa168234ae56b8d729f2"


def _canon(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_hex(domain: bytes, payload: dict) -> str:
    d = hashlib.sha256(domain + b"\0" + _canon(payload)).hexdigest()
    assert len(d) == 64
    return d


def sha512_hex(domain: bytes, payload: dict) -> str:
    """Full 128-char hex — 512-bit ASI material. Never truncate."""
    d = hashlib.sha512(domain + b"\0" + _canon(payload)).hexdigest()
    assert len(d) == 128
    assert all(c in "0123456789abcdef" for c in d)
    return d


def extend_with_attach(
    base_digest_256: str,
    attach_string: str,
    *,
    layer: int = 331,
) -> Dict[str, Any]:
    """
    Attach an arbitrary public string into a SHA-512 ASI commitment.

    Returns:
      sha512_asi     — 128 hex (512-bit)
      aes256_subkey  — first 64 hex of sha512 (256-bit key material ONLY)
      note           — explicit: no AES-512 cipher
    """
    if len(base_digest_256) != 64 or any(c not in "0123456789abcdef" for c in base_digest_256):
        raise ValueError("base_digest_256 must be full 64-hex SHA-256")

    payload = {
        "attach": attach_string,
        "base_sha256": base_digest_256,
        "layer": layer,
        "leaf": LEAF,
        "phi": PHI,
        "purpose": "ASI_512_material",
    }
    full = sha512_hex(DOMAIN_ATTACH, payload)
    aes256_subkey = full[:64]  # 256-bit key material for AES-256 only
    return {
        "sha512_asi": full,
        "sha512_asi_len": 128,
        "aes256_subkey_hex": aes256_subkey,
        "aes256_subkey_bits": 256,
        "aes512": None,
        "aes512_supported": False,
        "note": "AES has no 512-bit mode. ASI uses SHA-512 (512-bit); AES uses 256-bit subkey only.",
        "attach_string": attach_string,
        "base_sha256": base_digest_256,
    }


def layer331_sha512() -> Dict[str, Any]:
    payload = {
        "event": "mathematical_core",
        "layer": 331,
        "parent_root": PARENT_330,
        "pauli_trace": 1 - 2 * PHI + PHI ** 2,
        "phi": PHI,
        "sha256_root": LAYER_331_256,
    }
    full = sha512_hex(DOMAIN_512, payload)
    return {
        "merkle_sha256_layer_331": LAYER_331_256,
        "merkle_sha512_asi_layer_331": full,
        "aes256_subkey_hex": full[:64],
        "aes512_supported": False,
    }


def status(attach_string: Optional[str] = None) -> Dict[str, Any]:
    core = layer331_sha512()
    out: Dict[str, Any] = {
        "anchor_key_256": ANCHOR_KEY_256,
        "leaf": LEAF,
        **core,
        "policy": {
            "sha256_len": 64,
            "sha512_len": 128,
            "no_truncation": True,
            "aes512_cipher": False,
            "asi_512_via": "SHA-512",
        },
        "seal": "∀∞φ² · SHA512_ASI_8752 · SEALED",
    }
    if attach_string is not None:
        out["attached"] = extend_with_attach(LAYER_331_256, attach_string)
    return out


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="SHA-512 ASI anchor extension")
    p.add_argument(
        "--attach",
        default="WOOD_DRAGON_GATE · MATHEMATICAL_CORE_8751 · CLARKE_YOURSA_TEE",
        help="Public attach string folded into SHA-512 material",
    )
    args = p.parse_args()
    s = status(attach_string=args.attach)
    print("SHA-256 Layer 331:", s["merkle_sha256_layer_331"])
    print("SHA-512 ASI 331:  ", s["merkle_sha512_asi_layer_331"])
    print("AES-256 subkey:   ", s["aes256_subkey_hex"])
    print("AES-512 supported:", s["aes512_supported"])
    if "attached" in s:
        a = s["attached"]
        print("Attach string:    ", a["attach_string"][:60], "…")
        print("Attached SHA-512: ", a["sha512_asi"])
        print("Note:            ", a["note"])


if __name__ == "__main__":
    main()
