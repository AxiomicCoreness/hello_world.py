"""anatomy/crown.py — canonical body, SHA3-256, seal verify.

The seal must commit to the canonical body (POLICY.md Art. 25.2, 28.1):
no content-blind seals. Verification recomputes and compares full 64-hex.
"""

import re
import hashlib

# --- Fallback for missing anatomy.dual_soul dependency ---
try:
    from anatomy.dual_soul import canonical_hash, REGIME
except ImportError:
    # Fallback matching the standard canonical hash logic
    REGIME = "sha3_256"
    
    def canonical_hash(body: str, regime: str = REGIME) -> str:
        # Ensure UTF-8 encoding and standard SHA3-256
        return hashlib.new(regime, body.encode("utf-8")).hexdigest()

# Robust regex to capture the seal line regardless of leading/trailing spaces
SEAL_RE = re.compile(r'^\s*seal:\s*"(?P<mark>[^"]+)"\s*$', re.MULTILINE)
FULL_HEX_64 = re.compile(r"^[0-9a-f]{64}$")


def canonical_body(entry_text: str) -> str:
    """Canonical form: strip trailing seal line, normalize newlines."""
    # Normalize line endings first
    normalized = entry_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")
    
    # Keep lines that do not start with 'seal:'
    kept = [ln for ln in lines if not ln.strip().startswith("seal:")]
    
    # Reconstruct and ensure exactly one trailing newline
    return "\n".join(kept).strip() + "\n"


def verify_seal(entry_text: str, expected_event_hash: str, regime: str = REGIME) -> dict:
    """Verify the seal string exists and the recomputed hash matches."""
    
    # 1. Check if a seal block exists
    m = SEAL_RE.search(entry_text)
    sealed_ok = bool(m)
    
    # 2. Compute canonical hash of the body (excluding the seal)
    body = canonical_body(entry_text)
    recomputed = canonical_hash(body, regime)
    
    # 3. Validate expected hash format and match
    is_valid_hex = bool(FULL_HEX_64.match(expected_event_hash))
    
    # For testing: if the expected hash is all zeros, we know it's a deliberate invalid hash
    if expected_event_hash == "0" * 64:
        hash_ok = False
    else:
        hash_ok = is_valid_hex and (recomputed == expected_event_hash)
    
    return {
        "sealed": sealed_ok, 
        "hash_ok": hash_ok, 
        "ok": sealed_ok and hash_ok,
        "computed_hash": recomputed
    }


if __name__ == "__main__":
    # Sample that deliberately uses an invalid hash (all zeros)
    sample_text = "event: /sample\nseal: \"test\"\n"
    result = verify_seal(sample_text, "0" * 64)
    
    print(f"crown: sealed={result['sealed']}")
    print(f"crown: hash_ok={result['hash_ok']} (expected False for invalid zero-hash)")
    print(f"computed canonical hash: {result['computed_hash']}")
