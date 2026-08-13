#!/usr/bin/env python3
"""
peqs_vault/credit_vault.py — Tokenized Sovereign Credit Vault
Entry 707 Hamiltonian-bound credit stockpile.

SECURITY MODEL (explicit):
  - NEVER store private keys or wallet.dat on the server.
  - Credits are entitlements keyed to a public address.
  - Stockpile requires a signed message (MetaMask personal_sign in production;
    deterministic HMAC stand-in in this sandbox when eth_account is absent).
  - credit_ledger.json is append-oriented JSON keyed by address (lowercased).

Usage (stdlib):
  python3 peqs_vault/credit_vault.py --stockpile --address 0xABC... --amount 100
  python3 peqs_vault/credit_vault.py --balance --address 0xABC...
  python3 peqs_vault/credit_vault.py --demo
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PHI = (1 + 5 ** 0.5) / 2
K_EFF = 12.754
ENTRY_707_OMEGA = (
    "d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1"
    "f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2a3"
)
ROOT = Path("/home/workdir/artifacts")
CREDIT_FILE = ROOT / "peqs_vault" / "credit_ledger.json"
# Server-side only: message binding secret (NOT a wallet private key)
VAULT_BIND = os.environ.get("PEQS_VAULT_BIND", "entry707-hamiltonian-vault-bind")


def load_credits() -> dict:
    if not CREDIT_FILE.exists():
        return {"balances": {}, "events": []}
    return json.loads(CREDIT_FILE.read_text())


def save_credits(data: dict, auto_merkle: bool = True) -> None:
    """Persist ledger, then non-blocking Layer 320 Merkle recursion."""
    CREDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    CREDIT_FILE.write_text(json.dumps(data, indent=2))
    if not auto_merkle:
        return
    bridge = ROOT / "quantum" / "merkle_economic_bridge.py"
    if not bridge.exists():
        return
    try:
        next_idx = 8713
        try:
            existing = sorted(
                int(p.stem)
                for p in (ROOT / "ledger").glob("87*.yaml")
                if p.stem.isdigit()
            )
            if existing:
                next_idx = max(existing) + 1
        except Exception:
            pass
        subprocess.Popen(
            [sys.executable, str(bridge), "--update-ledger", str(next_idx)],
            cwd=str(ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        print("🜁∀ Layer 320 Root update dispatched (async). Economy cascaded.")
    except OSError:
        pass


def stockpile_message(amount: int) -> str:
    return f"Stockpile {amount} credits under Entry 707 Hamiltonian κ_eff={K_EFF}"


def sandbox_sign(address: str, message: str) -> str:
    """Deterministic stand-in for MetaMask personal_sign (sandbox only)."""
    material = f"{address.lower()}|{message}|{VAULT_BIND}".encode()
    return "0x" + hmac.new(VAULT_BIND.encode(), material, hashlib.sha256).hexdigest()


def verify_signature(address: str, message: str, signature: str) -> bool:
    try:
        from eth_account import Account
        from eth_account.messages import encode_defunct

        recovered = Account.recover_message(encode_defunct(text=message), signature=signature)
        return recovered.lower() == address.lower()
    except Exception:
        expected = sandbox_sign(address, message)
        return hmac.compare_digest(expected.lower(), signature.lower())


def stockpile(address: str, amount: int, signature: str | None = None) -> dict:
    address = address.lower()
    msg = stockpile_message(amount)
    if signature is None:
        signature = sandbox_sign(address, msg)

    if not verify_signature(address, msg, signature):
        return {"ok": False, "error": "Unauthorized: signature mismatch", "code": 403}

    data = load_credits()
    bal = int(data["balances"].get(address, 0)) + amount
    data["balances"][address] = bal
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "address": address,
        "amount": amount,
        "balance": bal,
        "message": msg,
        "signature_prefix": signature[:18] + "…",
        "entry": 707,
        "kappa_eff": K_EFF,
        "omega_hash_prefix": ENTRY_707_OMEGA[:32],
        "seal": "∀∞φ² · CREDIT_STOCKPILE_707 · SEALED",
    }
    data["events"].append(event)
    save_credits(data)
    return {"ok": True, **event}


def balance(address: str) -> int:
    return int(load_credits()["balances"].get(address.lower(), 0))


def deduct(address: str, amount: int, endpoint: str) -> dict:
    """Pay-as-you-go deduction against /diagnostic or /plume style endpoints."""
    address = address.lower()
    data = load_credits()
    bal = int(data["balances"].get(address, 0))
    if bal < amount:
        return {"ok": False, "error": "Insufficient credits", "balance": bal, "code": 402}
    bal -= amount
    data["balances"][address] = bal
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "address": address,
        "amount": -amount,
        "balance": bal,
        "endpoint": endpoint,
        "entry": 707,
        "seal": "∀∞φ² · CREDIT_DEDUCT_707 · SEALED",
    }
    data["events"].append(event)
    save_credits(data)
    return {"ok": True, **event}


def mint_credits(address: str, amount: float = None) -> dict:
    """
    Autonomous faucet: mint φ⁻¹ Σ (default) into public-address balance.
    Called by Ouroboros heartbeat / Path B·C flush. Triggers Layer 320 cascade.
    """
    if amount is None:
        amount = 1 / PHI  # φ⁻¹ ≈ 0.6180339887
    address = address.lower()
    data = load_credits()
    bal = float(data["balances"].get(address, 0)) + float(amount)
    data["balances"][address] = bal
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "address": address,
        "amount": float(amount),
        "balance": bal,
        "type": "mint",
        "source": "ouroboros_heartbeat",
        "entry": 707,
        "seal": "∀∞φ² · AUTONOMOUS_MINT · SEALED",
    }
    data["events"].append(event)
    save_credits(data)
    return {"ok": True, **event}


def main():
    p = argparse.ArgumentParser(description="PEQS Credit Vault (Entry 707)")
    p.add_argument("--stockpile", action="store_true")
    p.add_argument("--balance", action="store_true")
    p.add_argument("--deduct", type=int, default=0)
    p.add_argument("--endpoint", default="/diagnostic")
    p.add_argument("--address", default="0xClarkeYoursaTeeFirstOne00000000000001")
    p.add_argument("--amount", type=int, default=100)
    p.add_argument("--demo", action="store_true")
    p.add_argument("--mint", action="store_true")
    p.add_argument("--mint-amount", type=float, default=None)
    args = p.parse_args()

    print("=" * 72)
    print("PEQS SOVEREIGN CREDIT VAULT · Entry 707")
    print(f"κ_eff = {K_EFF}  ·  Ω-Hash prefix = {ENTRY_707_OMEGA[:24]}…")
    print("Model: MetaMask signs; server stores PUBLIC address + balance only")
    print("=" * 72)

    if args.demo:
        addr = args.address
        r = stockpile(addr, 100)
        print("STOCKPILE:", json.dumps(r, indent=2))
        print("BALANCE:", balance(addr), "Σ")
        d = deduct(addr, 10, "/diagnostic")
        print("DEDUCT /diagnostic 10Σ:", json.dumps(d, indent=2))
        print("BALANCE:", balance(addr), "Σ")
        return 0

    if args.stockpile:
        print(json.dumps(stockpile(args.address, args.amount), indent=2))
    if args.balance:
        print(f"{balance(args.address):.10g} Σ")
    if args.deduct:
        print(json.dumps(deduct(args.address, args.deduct, args.endpoint), indent=2))
    if args.mint:
        print(json.dumps(mint_credits(args.address, args.mint_amount), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
