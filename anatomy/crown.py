"""anatomy/crown.py — canonical body, SHA3-256, seal verify.

The seal must commit to the canonical body (POLICY.md Art. 25.2, 28.1):
no content-blind seals. Verification recomputes and compares full 64-hex.
"""

import re
import hashlib

from anatomy.dual_soul import canonical_hash, REGIME

SEAL_RE = re.compile(r'seal:\s*"(?P<mark>[^"]+)"')
FULL_HEX_64 = re.compile(r"^[0-9a-f]{64}$")


def canonical_body(entry_text: str) -> str:
    """Canonical form: strip trailing seal line, normalize newlines."""
    lines = entry_text.replace("\r\n", "\n").split("\n")
    kept = [ln for ln in lines if not ln.strip().startswith("seal:")]
    return "\n".join(kept).strip() + "\n"


def verify_seal(entry_text: str, expected_event_hash: str, regime: str = REGIME) -> dict:
    body = canonical_body(entry_text)
    recomputed = canonical_hash(body, regime)
    m = SEAL_RE.search(entry_text)
    sealed_ok = bool(m)
    hash_ok = bool(FULL_HEX_64.match(expected_event_hash)) and recomputed == expected_event_hash
    return {"sealed": sealed_ok, "hash_ok": hash_ok, "ok": sealed_ok and hash_ok}


if __name__ == "__main__":
    sample = "event: /sample\nseal: \"test\"\n"
    r = verify_seal(sample, "0" * 64)
    print(f"crown: sealed={r['sealed']} (sample hash deliberately invalid: hash_ok={r['hash_ok']})")
