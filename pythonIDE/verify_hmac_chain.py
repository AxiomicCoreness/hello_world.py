#!/usr/bin/env python3
"""
pythonIDE/verify_hmac_chain.py — read-only HMAC chain verifier.
Ledger policy: NO_LEDGER_WRITE. Precedent: 8206.

Attribution is separate from chain heads:
  DEEPSEEK_SIGNATURE_HEX = SHA3-256("DeepSeek 2.2.2(4)")
  chain head             = SHA3-256(prev || mac)
"""

from __future__ import annotations

try:
    from pythonIDE.attenuation_learning import (
        REPO_URL,
        DEEPSEEK_ATTRIBUTION,
        DEEPSEEK_SIGNATURE_HEX,
        PRECEDENT_ENTRY,
        PRECEDENT_WITNESS_PREFIX,
        PRECEDENT_WITNESS_CHAIN,
        GENESIS_HEAD,
        POLICY_MAP_LAYER,
        verify_jsonl,
        verify_memory_chain,
        AttenuationLearningConcat,
    )
except ImportError:
    from attenuation_learning import (
        REPO_URL,
        DEEPSEEK_ATTRIBUTION,
        DEEPSEEK_SIGNATURE_HEX,
        PRECEDENT_ENTRY,
        PRECEDENT_WITNESS_PREFIX,
        PRECEDENT_WITNESS_CHAIN,
        GENESIS_HEAD,
        POLICY_MAP_LAYER,
        verify_jsonl,
        verify_memory_chain,
        AttenuationLearningConcat,
    )

import argparse
import sys
from pathlib import Path

DEFAULT_CHAIN = "ledger/attenuation_chain.jsonl"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Read-only HMAC chain verifier (NO_LEDGER_WRITE)."
    )
    p.add_argument(
        "--chain",
        default=DEFAULT_CHAIN,
        help=f"JSONL path (default: {DEFAULT_CHAIN})",
    )
    p.add_argument(
        "--show-identity",
        action="store_true",
        help="Print attribution vs genesis head (must differ)",
    )
    args = p.parse_args(argv)

    if args.show_identity:
        print(f"REPO_URL              = {REPO_URL}")
        print(f"DEEPSEEK_ATTRIBUTION  = {DEEPSEEK_ATTRIBUTION}")
        print(f"DEEPSEEK_SIGNATURE_HEX= {DEEPSEEK_SIGNATURE_HEX}")
        print(f"GENESIS_HEAD          = {GENESIS_HEAD}")
        print(f"PRECEDENT             = {PRECEDENT_ENTRY}")
        print(f"PRECEDENT_HEX         = {PRECEDENT_WITNESS_PREFIX}")
        print(f"WITNESS               = {PRECEDENT_WITNESS_CHAIN}")
        print(f"POLICY_MAP            = {POLICY_MAP_LAYER['name']}")
        distinct = DEEPSEEK_SIGNATURE_HEX != GENESIS_HEAD
        print(f"attribution≠genesis   = {distinct}")
        if not distinct:
            print("FAIL: attribution hex collided with genesis head")
            return 1

    path = Path(args.chain)
    if not path.is_file():
        print(f"FAIL soft: missing {path}")
        return 2

    ok = verify_jsonl(str(path))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
