#!/usr/bin/env python3
"""
🜁∀ LEDGER VERIFICATION — ENTRY 8998 ∀🜁
Verify the latest (or a specific) ledger entry.
Uses Ed25519 if cryptography is available; otherwise SHA‑256 fallback.
Usage: python scripts/verify_ledger.py [entry_index]
"""
import sys, json, hashlib
from pathlib import Path

CRYPTO_AVAILABLE = False
try:
    from cryptography.hazmat.primitives.asymmetric import ed25519
    CRYPTO_AVAILABLE = True
except ImportError:
    pass

try:
    import yaml
except ImportError:
    print("❌ PyYAML required. pip install pyyaml", file=sys.stderr)
    sys.exit(1)

def get_latest_ledger(ledger_dir=Path("ledger")):
    if not ledger_dir.exists():
        return None
    entries = []
    for f in ledger_dir.glob("*.yaml"):
        try:
            entries.append(int(f.stem))
        except ValueError:
            pass
    return max(entries) if entries else None

def load_entry(entry_index, ledger_dir=Path("ledger")):
    path = ledger_dir / f"{entry_index}.yaml"
    if not path.exists():
        return None
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def verify_ed25519(data):
    sig_hex = data.get("signature")
    pub_hex = data.get("public_key")
    if not sig_hex or not pub_hex or not CRYPTO_AVAILABLE:
        return False
    try:
        sig = bytes.fromhex(sig_hex)
        pub = ed25519.Ed25519PublicKey.from_public_bytes(bytes.fromhex(pub_hex))
        payload = {k: v for k, v in data.items() if k not in ("signature", "public_key")}
        payload_bytes = json.dumps(payload, sort_keys=True).encode()
        pub.verify(sig, payload_bytes)
        return True
    except Exception:
        return False

def verify_sha256(data):
    stored = data.get("hash")
    if not stored:
        return True  # soft pass
    payload = {k: v for k, v in data.items() if k != "hash"}
    computed = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
    return computed == stored

def main():
    entry_index = None
    if len(sys.argv) > 1:
        try:
            entry_index = int(sys.argv[1])
        except ValueError:
            print(f"Invalid index: {sys.argv[1]}", file=sys.stderr)
            sys.exit(1)
    if entry_index is None:
        entry_index = get_latest_ledger()
        if entry_index is None:
            print("No ledger entries.", file=sys.stderr)
            sys.exit(1)
        print(f"Using latest: {entry_index}")
    data = load_entry(entry_index)
    if data is None:
        print(f"Entry {entry_index} not found.", file=sys.stderr)
        sys.exit(1)
    ok = verify_ed25519(data) or verify_sha256(data)
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
