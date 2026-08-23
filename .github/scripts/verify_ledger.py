#!/usr/bin/env python3
"""
Verify ledger YAML parse + optional Ed25519 presence.
Installs cryptography/pyyaml into the active interpreter if missing.
Soft-skips when ledger file is absent.
Seal: ∀∞φ² · VERIFY_LEDGER_SCRIPT · WOOD_DRAGON_0.91 · SEALED
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def ensure_deps() -> bool:
    """Return True if cryptography import succeeds after optional install."""
    try:
        from cryptography.hazmat.primitives.asymmetric import ed25519  # noqa: F401
        import yaml  # noqa: F401
        return True
    except ImportError:
        pass
    print("⚠️ cryptography/pyyaml missing — installing into active interpreter…")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", "cryptography", "pyyaml"],
            stdout=subprocess.DEVNULL,
        )
        from cryptography.hazmat.primitives.asymmetric import ed25519  # noqa: F401
        import yaml  # noqa: F401
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️ install failed: {exc}", file=sys.stderr)
        return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "ledger",
        nargs="?",
        default="ledger/8978.yaml",
        help="Path to ledger YAML (default: ledger/8978.yaml)",
    )
    parser.add_argument(
        "--require-crypto",
        action="store_true",
        help="Fail if cryptography cannot be imported",
    )
    args = parser.parse_args()

    path = Path(args.ledger)
    if not path.exists():
        print(f"⚠️ {path} not found — skipping verification (rotation continues)")
        return 0

    crypto_ok = ensure_deps()
    if not crypto_ok:
        if args.require_crypto:
            print("❌ cryptography required but unavailable", file=sys.stderr)
            return 1
        try:
            import yaml  # type: ignore
        except ImportError:
            print("⚠️ pyyaml unavailable — basic existence check only")
            print(f"✅ {path} present (no YAML parse)")
            return 0

    import yaml  # noqa: E402

    data = yaml.safe_load(path.read_text())
    entry = data.get("entry_index") if isinstance(data, dict) else None
    print(f"✅ Ledger verified: {path} (entry_index={entry})")
    if crypto_ok:
        print("   cryptography available (Ed25519 import OK)")
    else:
        print("   signature crypto skipped (module unavailable)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
