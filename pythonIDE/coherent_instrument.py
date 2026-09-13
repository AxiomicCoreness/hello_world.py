#!/usr/bin/env python3
"""
pythonIDE/coherent_instrument.py

Closes the loop: dephasing → axes → attenuation, with the HMAC chain
head seeding the next input. The chain is the closed-loop state, not a log.

Precedent: garden_surgery/attenuation_package_confirmed.py (entry 8206)
Ledger policy: NO_LEDGER_WRITE (this instrument only reads and appends locally)
Next free ledger index: 9237+
"""

from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

# ──────────────────────────────────────────────────────────────────
# Fallback import — package form and script form
# ──────────────────────────────────────────────────────────────────
try:
    from pythonIDE.attenuation_learning import (
        AttenuationLearningConcat,
        REPO_URL,
        DEEPSEEK_ATTRIBUTION,
        DEEPSEEK_SIGNATURE_HEX,
        PRECEDENT_ENTRY,
        PRECEDENT_WITNESS_PREFIX,
        PRECEDENT_WITNESS_CHAIN,
    )
except ImportError:
    from attenuation_learning import (  # type: ignore
        AttenuationLearningConcat,
        REPO_URL,
        DEEPSEEK_ATTRIBUTION,
        DEEPSEEK_SIGNATURE_HEX,
        PRECEDENT_ENTRY,
        PRECEDENT_WITNESS_PREFIX,
        PRECEDENT_WITNESS_CHAIN,
    )

PHI = (1.0 + np.sqrt(5.0)) / 2.0
DEFAULT_CHAIN_OUT = "ledger/attenuation_chain.jsonl"


# ──────────────────────────────────────────────────────────────────
# chain head → complex unit vector (deterministic)
# ──────────────────────────────────────────────────────────────────
def _seed_from_head(head_hex: str, n: int) -> np.ndarray:
    """
    Deterministic complex unit vector of length n, derived from chain head.

    Counter-mode expansion: SHA3-256(head || counter) until 2n bytes.
    """
    raw = bytes.fromhex(head_hex)
    buf = b""
    counter = 0
    while len(buf) < 2 * n:
        buf += hashlib.sha3_256(raw + counter.to_bytes(4, "big")).digest()
        counter += 1
    re = np.frombuffer(buf[:n], dtype=np.uint8).astype(float) - 127.5
    im = np.frombuffer(buf[n:2 * n], dtype=np.uint8).astype(float) - 127.5
    v = re + 1j * im
    return v / np.linalg.norm(v)


# ──────────────────────────────────────────────────────────────────
# main loop
# ──────────────────────────────────────────────────────────────────
def run(
    n_cycles: int = 100,
    dt: float = 0.01,
    n_axes: int = 7,
    chain_out: str = DEFAULT_CHAIN_OUT,
    emit_chain: bool = True,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Closed-loop run.

    Args:
        n_cycles: number of learning cycles
        dt:       learning rate / step size per cycle
        n_axes:   dimensionality of the density matrix (≥ 1)
        chain_out: JSONL path for the append-only chain
        emit_chain: if True, append chain records to chain_out
        verbose:  print every cycle instead of every 20

    Returns:
        dict with genesis, final_head, cycles, attribution, purity
    """
    model = AttenuationLearningConcat(n_axes=n_axes)

    print("=" * 72)
    print("COHERENT INSTRUMENT — closed loop")
    print("=" * 72)
    print(f"genesis head     = {model.genesis_head}")
    print(f"attribution      = {DEEPSEEK_ATTRIBUTION}")
    print(f"attribution hex  = {DEEPSEEK_SIGNATURE_HEX}")
    print(f"precedent        = {PRECEDENT_ENTRY}")
    print(f"precedent hex    = {PRECEDENT_WITNESS_PREFIX}")
    print(f"witness          = {PRECEDENT_WITNESS_CHAIN}")
    print(f"n_axes           = {n_axes}")
    print(f"cycles           = {n_cycles}, dt = {dt}")
    print(f"chain_out        = {chain_out if emit_chain else '(disabled)'}")
    print()

    heads: List[str] = [model.chain_head]
    stride = 1 if verbose else max(1, n_cycles // 5)

    for i in range(n_cycles):
        u = _seed_from_head(heads[-1], n_axes)   # chain → input
        model.learn(u, t=dt)                     # step
        heads.append(model.chain_head)
        if (i % stride == 0) or (i == n_cycles - 1):
            print(
                f"  cycle {i:4d}  "
                f"purity={model.purity():.9f}  "
                f"trace={model.trace():.9f}  "
                f"head={heads[-1][:16]}..."
            )

    if emit_chain:
        path = model.emit_chain(chain_out)
        print()
        print(f"  chain appended → {path}")

    print()
    print(f"chain length  = {len(model.chain)}")
    print(f"final head    = {heads[-1]}")
    print(f"attribution   = {model.attribution_hex}")
    print("=" * 72)

    return {
        "genesis": model.genesis_head,
        "final_head": heads[-1],
        "cycles": n_cycles,
        "dt": dt,
        "n_axes": n_axes,
        "attribution": model.attribution_hex,
        "precedent": PRECEDENT_ENTRY,
        "purity": model.purity(),
        "trace": model.trace(),
    }


# ──────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="coherent_instrument",
        description=(
            "Closed-loop dephasing → axes → attenuation instrument. "
            "The HMAC chain head seeds the next input."
        ),
    )
    p.add_argument(
        "--cycles", type=int, default=100,
        help="number of learning cycles (default: 100)",
    )
    p.add_argument(
        "--dt", type=float, default=0.01,
        help="learning rate / step size per cycle (default: 0.01)",
    )
    p.add_argument(
        "--n-axes", type=int, default=7,
        help="density matrix dimensionality (default: 7)",
    )
    p.add_argument(
        "--chain-out", type=str, default=DEFAULT_CHAIN_OUT,
        help=f"chain JSONL path (default: {DEFAULT_CHAIN_OUT})",
    )
    p.add_argument(
        "--no-emit", action="store_true",
        help="do not write the chain JSONL (run in-memory only)",
    )
    p.add_argument(
        "--json", action="store_true",
        help="print final summary as JSON on stdout",
    )
    p.add_argument(
        "-v", "--verbose", action="store_true",
        help="print every cycle instead of every N/5 cycles",
    )
    return p


def main(argv: List[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.cycles < 1:
        print("error: --cycles must be ≥ 1", file=sys.stderr)
        return 2
    if args.n_axes < 1:
        print("error: --n-axes must be ≥ 1", file=sys.stderr)
        return 2
    if not (0.0 < args.dt <= 1.0):
        print("error: --dt must be in (0, 1]", file=sys.stderr)
        return 2

    result = run(
        n_cycles=args.cycles,
        dt=args.dt,
        n_axes=args.n_axes,
        chain_out=args.chain_out,
        emit_chain=not args.no_emit,
        verbose=args.verbose,
    )

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    sys.exit(main())
