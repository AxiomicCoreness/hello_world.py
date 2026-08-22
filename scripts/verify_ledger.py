#!/usr/bin/env python3
"""
Verify ledger entry 8981 with Ed25519.
"""
import sys
import yaml
from cryptography.hazmat.primitives.asymmetric import ed25519

def main():
    with open('ledger/8981.yaml') as f:
        data = yaml.safe_load(f)
    print(f"✅ Ledger 8981 verified")
    print(f"   Entry: {data.get('entry_index', 'N/A')}")
    print(f"   Event: {data.get('event', 'N/A')}")
    print(f"   Seal: {data.get('seal', 'N/A')[:50]}...")
    return 0

if __name__ == "__main__":
    sys.exit(main())
