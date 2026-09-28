"""anatomy/dual_soul.py — regime-dependent equality.

Two entries are equal only under the declared hash regime
(POLICY.md Art. 27: hash_regime authority; Art. 32: universal equality).
A body and its hash are never conflated.
"""

import hashlib

REGIME = "GARDEN.EVENT.v1"


def canonical_hash(body: str, regime: str = REGIME) -> str:
    """SHA3-256 over regime | 0x00 | body (domain separation)."""
    return hashlib.sha3_256(regime.encode() + b"\x00" + body.encode()).hexdigest()


def equal(a: str, b: str, regime_a: str = REGIME, regime_b: str = REGIME) -> bool:
    """Regime-dependent equality: identical only if same regime AND same canonical hash."""
    if regime_a != regime_b:
        return False
    return canonical_hash(a, regime_a) == canonical_hash(b, regime_b)


if __name__ == "__main__":
    h = canonical_hash("test-body")
    print(f"dual_soul: regime={REGIME} sample_hash={h[:16]}…")
