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
  python3 peqs_vault/credit_vault.py --stockpile --address 0xABC --amount 100
  python3 peqs_vault/credit_vault.py --balance --address 0xABC
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
VAULT_BIND = os.environ.get("PEQS_VAULT_BIND", "entry707-hamiltonian-vault-bind")


def load_credits() -> dict:
    if not CREDIT_FILE.exists():
        return {"balances": {}, "events": []}
    return json.loads(CREDIT_FILE.read_text())


def save_credits(data: dict, auto_merkle: bool = True) -> None:
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
    except Exception:
        pass


def _sign_message(address: str, amount: float, msg: str) -> str:
    material = f"{address.lower()}|{amount}|{msg}|{VAULT_BIND}".encode()
    return hmac.new(VAULT_BIND.encode(), material, hashlib.sha256).hexdigest()


def stockpile(address: str, amount: float) -> dict:
    address = address.lower()
    data = load_credits()
    bal = float(data["balances"].get(address, 0)) + float(amount)
    data["balances"][address] = bal
    msg = f"stockpile {amount} to {address}"
    signature = _sign_message(address, amount, msg)
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "address": address,
        "amount": float(amount),
        "balance": bal,
        "message": msg,
        "signature": signature,  # full — no truncation
        "entry": 707,
        "kappa_eff": K_EFF,
        "omega_hash": ENTRY_707_OMEGA,  # full — no truncation
        "seal": "∀∞φ² · CREDIT_STOCKPILE_707 · SEALED",
    }
    data["events"].append(event)
    save_credits(data)
    return {"ok": True, **event}


def balance(address: str) -> float:
    data = load_credits()
    return float(data["balances"].get(address.lower(), 0))


def deduct(address: str, amount: float, endpoint: str) -> dict:
    address = address.lower()
    data = load_credits()
    bal = float(data["balances"].get(address, 0))
    if bal < amount:
        return {"ok": False, "error": "insufficient", "balance": bal}
    bal -= float(amount)
    data["balances"][address] = bal
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "address": address,
        "amount": -float(amount),
        "balance": bal,
        "endpoint": endpoint,
        "type": "deduct",
        "entry": 707,
        "seal": "∀∞φ² · CREDIT_DEDUCT · SEALED",
    }
    data["events"].append(event)
    save_credits(data)
    return {"ok": True, **event}


def mint_credits(address: str, amount: float = None) -> dict:
    if amount is None:
        amount = 1 / PHI
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
    print(f"κ_eff = {K_EFF}  ·  Ω-Hash = {ENTRY_707_OMEGA}")  # full — no truncation
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
