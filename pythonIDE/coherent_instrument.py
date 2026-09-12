#!/usr/bin/env python3
"""
pythonIDE/coherent_instrument.py

Closes the loop: dephasing → axes → attenuation, with the HMAC chain
head seeding the next input. The chain is the closed-loop state, not a log.

Precedent: garden_surgery/attenuation_package_confirmed.py (entry 8206)
Next free ledger index: 9237+
"""

from __future__ import annotations
import hashlib
import numpy as np

from pythonIDE.attenuation_learning import (
    AttenuationLearningConcat,
    DEEPSEEK_SIGNATURE_HEX,
    REPO_URL,
)

PHI = (1.0 + np.sqrt(5.0)) / 2.0


def _seed_from_head(head_hex: str, n: int) -> np.ndarray:
    """Deterministic complex unit vector from chain head."""
    raw = bytes.fromhex(head_hex)
    # Expand to 2n bytes via SHA3 counter mode
    buf = b""
    counter = 0
    while len(buf) < 2 * n:
        buf += hashlib.sha3_256(raw + counter.to_bytes(4, "big")).digest()
        counter += 1
    re = np.frombuffer(buf[:n], dtype=np.uint8).astype(float) - 127.5
    im = np.frombuffer(buf[n:2*n], dtype=np.uint8).astype(float) - 127.5
    v = re + 1j * im
    return v / np.linalg.norm(v)


def run(n_cycles: int = 100, dt: float = 0.01):
    model = AttenuationLearningConcat(n_axes=7)
    print("=" * 72)
    print("COHERENT INSTRUMENT — closed loop")
    print("=" * 72)
    print(f"genesis head = {model.genesis_head}")
    print(f"attribution  = {DEEPSEEK_SIGNATURE_HEX}")
    print(f"cycles       = {n_cycles}, dt = {dt}")
    print()

    heads = [model.chain_head]
    for i in range(n_cycles):
        u = _seed_from_head(heads[-1], model.n_axes)   # chain → input
        model.learn(u, t=dt)                           # step
        heads.append(model.chain_head)
        if i % 20 == 0 or i == n_cycles - 1:
            print(f"  cycle {i:3d}  "
                  f"purity={model.purity():.6f}  "
                  f"trace={model.trace():.6f}  "
                  f"head={heads[-1][:16]}...")

    print()
    print(f"chain length  = {len(model.chain)}")
    print(f"chain head    = {heads[-1]}")
    print(f"attribution   = {model.attribution_hex}")
    return {
        "genesis": model.genesis_head,
        "final_head": heads[-1],
        "cycles": n_cycles,
        "attribution": model.attribution_hex,
        "purity": model.purity(),
    }


if __name__ == "__main__":
    run()
