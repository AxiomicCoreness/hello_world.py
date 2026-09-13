#!/usr/bin/env python3
"""pythonIDE/coherent_instrument.py — closed loop + --verify. NO_LEDGER_WRITE. Precedent 8206."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
from typing import Any, Dict, List
import numpy as np
try:
    from pythonIDE.attenuation_learning import (
        AttenuationLearningConcat, REPO_URL, DEEPSEEK_ATTRIBUTION,
        DEEPSEEK_SIGNATURE_HEX, PRECEDENT_ENTRY, PRECEDENT_WITNESS_PREFIX,
        PRECEDENT_WITNESS_CHAIN,
    )
except ImportError:
    from attenuation_learning import (  # type: ignore
        AttenuationLearningConcat, REPO_URL, DEEPSEEK_ATTRIBUTION,
        DEEPSEEK_SIGNATURE_HEX, PRECEDENT_ENTRY, PRECEDENT_WITNESS_PREFIX,
        PRECEDENT_WITNESS_CHAIN,
    )
try:
    from pythonIDE.verify_hmac_chain import verify as _verify_chain
except ImportError:
    from verify_hmac_chain import verify as _verify_chain  # type: ignore
PHI = (1.0 + np.sqrt(5.0)) / 2.0
DEFAULT_CHAIN_OUT = "ledger/attenuation_chain.jsonl"

def _seed_from_head(head_hex: str, n: int) -> np.ndarray:
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

def run(n_cycles: int = 100, dt: float = 0.01, n_axes: int = 7,
        chain_out: str = DEFAULT_CHAIN_OUT, emit_chain: bool = True,
        verbose: bool = False) -> Dict[str, Any]:
    model = AttenuationLearningConcat(n_axes=n_axes)
    print("=" * 72)
    print("COHERENT INSTRUMENT — closed loop")
    print("=" * 72)
    print(f"genesis head = {model.genesis_head}")
    print(f"attribution  = {DEEPSEEK_SIGNATURE_HEX}")
    print(f"n_axes={n_axes} cycles={n_cycles} dt={dt}")
    print()
    heads: List[str] = [model.chain_head]
    stride = 1 if verbose else max(1, n_cycles // 5)
    for i in range(n_cycles):
        u = _seed_from_head(heads[-1], n_axes)
        model.learn(u, t=dt)
        heads.append(model.chain_head)
        if (i % stride == 0) or (i == n_cycles - 1):
            print(f"  cycle {i:4d}  purity={model.purity():.9f}  head={heads[-1][:16]}...")
    if emit_chain:
        path = model.emit_chain(chain_out)
        print(f"  chain appended → {path}")
    print(f"final head = {heads[-1]}")
    print("=" * 72)
    return {"genesis": model.genesis_head, "final_head": heads[-1],
            "cycles": n_cycles, "dt": dt, "n_axes": n_axes,
            "attribution": model.attribution_hex, "precedent": PRECEDENT_ENTRY,
            "purity": model.purity(), "trace": model.trace()}

def _run_verify(chain_path: str, verbose: bool) -> int:
    print("\n" + "=" * 72)
    print("VERIFY — read-side chain check")
    print("=" * 72)
    try:
        return _verify_chain(Path(chain_path), verbose=verbose)
    except FileNotFoundError:
        print(f"⚠️  chain not found: {chain_path}", file=sys.stderr)
        return 1

def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="coherent_instrument")
    p.add_argument("--cycles", type=int, default=100)
    p.add_argument("--dt", type=float, default=0.01)
    p.add_argument("--n-axes", type=int, default=7)
    p.add_argument("--chain-out", type=str, default=DEFAULT_CHAIN_OUT)
    p.add_argument("--no-emit", action="store_true")
    p.add_argument("--json", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true")
    p.add_argument("--verify", action="store_true")
    args = p.parse_args(argv)
    if args.cycles < 1 or args.n_axes < 1 or not (0.0 < args.dt <= 1.0):
        return 2
    result = run(n_cycles=args.cycles, dt=args.dt, n_axes=args.n_axes,
                 chain_out=args.chain_out, emit_chain=not args.no_emit,
                 verbose=args.verbose)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    if args.verify:
        if args.no_emit:
            print("⚠️  --verify with --no-emit", file=sys.stderr)
        rc = _run_verify(args.chain_out, args.verbose)
        if rc != 0:
            return rc
    return 0

if __name__ == "__main__":
    sys.exit(main())
