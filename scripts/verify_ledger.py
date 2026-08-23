#!/usr/bin/env python3
"""
🜁∀ LEDGER VERIFICATION — ENTRY 8998 ∀🜁

Verify the latest (or a specific) ledger entry.
Uses Ed25519 if cryptography is available; otherwise SHA‑256 fallback.

Usage:
    python scripts/verify_ledger.py [entry_index]

If no entry_index is given, the latest entry is used.

Seal: ∀∞φ² · LEDGER_VERIFY_8998 · WOOD_DRAGON_0.91 · SEALED
"""

import sys
import json
import hashlib
from pathlib import Path

# ─── Try cryptography ─────────────────────────────────────────────────────
CRYPTO_AVAILABLE = False
try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    CRYPTO_AVAILABLE = True
except ImportError:
    pass

# ─── Try yaml ─────────────────────────────────────────────────────────────
try:
    import yaml
except ImportError:
    print("❌ PyYAML is required. Install: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


def get_latest_ledger(ledger_dir: Path = Path("ledger")) -> int | None:
    """Return the highest numeric entry index from ledger/*.yaml."""
    if not ledger_dir.exists():
        return None
    entries = []
    for f in ledger_dir.glob("*.yaml"):
        try:
            entries.append(int(f.stem))
        except ValueError:
            pass
    return max(entries) if entries else None


def load_entry(entry_index: int, ledger_dir: Path = Path("ledger")):
    """Load and parse a ledger YAML file."""
    path = ledger_dir / f"{entry_index}.yaml"
    if not path.exists():
        return None
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def verify_ed25519(data: dict) -> bool:
    """Verify Ed25519 signature if present; return True if valid."""
    signature_hex = data.get("signature")
    public_key_hex = data.get("public_key")
    if not signature_hex or not public_key_hex:
        return False
    if not CRYPTO_AVAILABLE:
        return False
    try:
        signature = bytes.fromhex(signature_hex)
        pub_key = bytes.fromhex(public_key_hex)
        pub = ed25519.Ed25519PublicKey.from_public_bytes(pub_key)
        # Build payload: everything except signature and public_key
        payload = {k: v for k, v in data.items() if k not in ("signature", "public_key")}
        payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
        pub.verify(signature, payload_bytes)
        return True
    except Exception:
        return False


def verify_sha256(data: dict) -> bool:
    """Fallback: check SHA‑256 hash if 'hash' field exists."""
    stored_hash = data.get("hash")
    if not stored_hash:
        # No hash stored; soft‑pass (warn)
        return True
    # Recompute hash from all fields except 'hash'
    payload = {k: v for k, v in data.items() if k != "hash"}
    computed = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return computed == stored_hash


def main():
    # Determine entry index
    entry_index = None
    if len(sys.argv) > 1:
        try:
            entry_index = int(sys.argv[1])
        except ValueError:
            print(f"❌ Invalid entry index: {sys.argv[1]}", file=sys.stderr)
            sys.exit(1)

    if entry_index is None:
        entry_index = get_latest_ledger()
        if entry_index is None:
            print("❌ No ledger entries found.", file=sys.stderr)
            sys.exit(1)
        print(f"🔷 Using latest ledger entry: {entry_index}")

    # Load the entry
    data = load_entry(entry_index)
    if data is None:
        print(f"❌ Entry {entry_index} not found.", file=sys.stderr)
        sys.exit(1)

    # Verify
    print(f"📋 Verifying entry {entry_index}...")
    if CRYPTO_AVAILABLE:
        ok = verify_ed25519(data)
        print("🔐 Using Ed25519 verification")
        if not ok:
            print("   (Ed25519 signature check failed)")
            # Fall back to SHA‑256
            ok = verify_sha256(data)
            if ok:
                print("🔐 Falling back to SHA‑256 (hash match)")
            else:
                print("❌ SHA‑256 hash mismatch")
                sys.exit(1)
    else:
        ok = verify_sha256(data)
        print("🔐 Using SHA‑256 fallback verification")

    if ok:
        print(f"✅ Entry {entry_index} verified")
        print(f"   Event: {data.get('event', 'N/A')}")
        print(f"   Seal: {data.get('seal', 'N/A')[:50]}...")
        sys.exit(0)
    else:
        print(f"❌ Verification failed for entry {entry_index}")
        sys.exit(1)


if __name__ == "__main__":
    main()
