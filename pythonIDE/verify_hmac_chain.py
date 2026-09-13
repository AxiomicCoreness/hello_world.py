#!/usr/bin/env python3
"""pythonIDE/verify_hmac_chain.py — read-only HMAC chain verifier. NO_LEDGER_WRITE. Precedent: 8206."""
from __future__ import annotations
try:
    from pythonIDE.attenuation_learning import (
        REPO_URL, DEEPSEEK_ATTRIBUTION, DEEPSEEK_SIGNATURE_HEX,
        PRECEDENT_ENTRY, PRECEDENT_WITNESS_PREFIX, PRECEDENT_WITNESS_CHAIN,
        GENESIS_HEAD, POLICY_MAP_LAYER, verify_jsonl, verify_memory_chain,
        AttenuationLearningConcat,
    )
except ImportError:
    from attenuation_learning import (
        REPO_URL, DEEPSEEK_ATTRIBUTION, DEEPSEEK_SIGNATURE_HEX,
        PRECEDENT_ENTRY, PRECEDENT_WITNESS_PREFIX, PRECEDENT_WITNESS_CHAIN,
        GENESIS_HEAD, POLICY_MAP_LAYER, verify_jsonl, verify_memory_chain,
        AttenuationLearningConcat,
    )
import argparse, sys
from pathlib import Path
from typing import Union
DEFAULT_CHAIN = "ledger/attenuation_chain.jsonl"

def verify(chain_path: Union[str, Path], verbose: bool = False) -> int:
    path = Path(chain_path)
    if not path.is_file():
        print(f"FAIL soft: missing {path}")
        return 2
    if verbose:
        print(f"verifying {path}")
    return 0 if verify_jsonl(str(path)) else 1

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Read-only HMAC chain verifier (NO_LEDGER_WRITE).")
    p.add_argument("--chain", default=DEFAULT_CHAIN)
    p.add_argument("--show-identity", action="store_true")
    p.add_argument("-v", "--verbose", action="store_true")
    args = p.parse_args(argv)
    if args.show_identity:
        print(f"REPO_URL={REPO_URL}")
        print(f"DEEPSEEK_SIGNATURE_HEX={DEEPSEEK_SIGNATURE_HEX}")
        print(f"GENESIS_HEAD={GENESIS_HEAD}")
        if DEEPSEEK_SIGNATURE_HEX == GENESIS_HEAD:
            return 1
    return verify(args.chain, verbose=args.verbose)

if __name__ == "__main__":
    sys.exit(main())
