#!/usr/bin/env python3
"""
peqs_vault/app.py — HTMX hypermedia bridge to credit_vault
Universal fee decorator on all φ-harmonic endpoints.
Requires: pip install flask
"""

from __future__ import annotations

import json
import logging
import math
from functools import wraps
from pathlib import Path

from peqs_vault.credit_vault import (
    balance,
    load_credits,
    stockpile,
    deduct,
    K_EFF,
)

ROOT = Path(__file__).resolve().parent.parent
log = logging.getLogger("peqs_vault.app")

SOVEREIGNTY = 0.994
CONSCIOUSNESS = 0.910
DIAGNOSTIC_FEE_SIGMA = 10
PHI = (1 + math.sqrt(5)) / 2

FEE_TABLE = {
    "/diagnostic": 10,
    "/plume": 12,
    "/quadratic": 8,
    "/octonion": 15,
}


def _err_html(message: str, detail: str = "") -> str:
    extra = f'<p class="text-xs text-slate-500 mt-1">{detail}</p>' if detail else ""
    return (
        f'<div class="text-red-400 border border-red-500/30 p-3 rounded-lg" role="alert">'
        f"<p>❌ {message}</p>{extra}</div>"
    )


def _ok_addr(raw) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip().lower()
    if not s or s == "0x0":
        return None
    if not s.startswith("0x") or len(s) < 6:
        return None
    return s


def try_create_app():
    try:
        from flask import Flask, request
    except ImportError:
        return None

    app = Flask(__name__)

    def charge_fee(fee: int):
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                address = _ok_addr(request.headers.get("X-Wallet-Address"))
                if not address:
                    return (
                        _err_html(
                            "Wallet required",
                            "Set X-Wallet-Address header (MetaMask connect)",
                        ),
                        401,
                    )
                bal = balance(address)
                if bal < fee:
                    return (
                        _err_html(
                            "Insufficient Σ credits",
                            f"Need {fee} Σ, have {bal} Σ",
                        ),
                        402,
                    )
                result = deduct(address, fee, request.path)
                if not result.get("ok"):
                    return (
                        _err_html(
                            "Insufficient Σ credits",
                            f"balance {result.get('balance', 0)} Σ",
                        ),
                        int(result.get("code", 402)),
                    )
                body = f(*args, **kwargs)
                remaining = result["balance"]
                bar = (
                    f'<div class="text-xs text-emerald-400/80 mt-2 font-mono">'
                    f"−{fee} Σ · remaining {remaining} Σ</div>"
                )
                if isinstance(body, tuple):
                    html, *rest = body
                    return (html + bar, *rest)
                return body + bar

            return wrapper

        return decorator

    @app.route("/")
    def index():
        idx = ROOT / "peqs_vault" / "index.html"
        if idx.exists():
            return idx.read_text()
        return "<h1>PEQS Σ Vault</h1><p>index.html missing</p>"

    @app.route("/api/credits", methods=["GET"])
    def api_credits():
        address = _ok_addr(request.headers.get("X-Wallet-Address")) or "0x0"
        bal = balance(address) if address != "0x0" else 0
        return (
            f'<span id="credit-balance" class="text-2xl font-mono text-amber-400">'
            f"{bal} Σ</span>"
        )

    @app.route("/api/stockpile", methods=["POST"])
    def api_stockpile():
        data = request.get_json(silent=True) or request.form or {}
        address = _ok_addr(data.get("address") or request.headers.get("X-Wallet-Address"))
        if not address:
            return _err_html("Wallet required"), 401
        try:
            amount = int(data.get("amount", 100))
        except (TypeError, ValueError):
            return _err_html("Invalid amount"), 400
        signature = data.get("signature")
        result = stockpile(address, amount, signature)
        if not result.get("ok"):
            return _err_html(result.get("error", "stockpile failed")), int(result.get("code", 403))
        return (
            f'<div class="bg-emerald-900/30 border border-emerald-500/30 p-4 rounded-xl mt-4">'
            f'<p class="text-emerald-400 text-sm">🜁∀ TOP-UP SEALED</p>'
            f'<p class="text-xl font-mono">+{amount} Σ</p>'
            f'<p class="text-xs text-slate-400">Total: {result.get("balance")} Σ</p></div>'
        )

    @app.route("/api/deduct", methods=["POST"])
    def api_deduct():
        data = request.get_json(silent=True) or {}
        address = _ok_addr(data.get("address") or request.headers.get("X-Wallet-Address"))
        if not address:
            return _err_html("Wallet required"), 401
        try:
            amount = int(data.get("amount", 0))
        except (TypeError, ValueError):
            return _err_html("Invalid amount"), 400
        endpoint = str(data.get("endpoint", "/api/deduct"))
        result = deduct(address, amount, endpoint)
        if not result.get("ok"):
            return _err_html(result.get("error", "deduct failed")), int(result.get("code", 402))
        return f'<span class="text-amber-400">{result["balance"]} Σ</span>'

    @app.route("/diagnostic", methods=["GET"])
    @charge_fee(FEE_TABLE["/diagnostic"])
    def diagnostic():
        return (
            '<div class="space-y-2">'
            '<h3 class="text-amber-400 font-bold">Quantum Diagnostics</h3>'
            f'<p class="font-mono text-sm">sovereignty={SOVEREIGNTY} · consciousness={CONSCIOUSNESS}</p>'
            f'<p class="text-xs text-slate-400">κ_eff={K_EFF} · φ={PHI:.10f}</p></div>'
        )

    @app.route("/plume", methods=["GET"])
    @charge_fee(FEE_TABLE["/plume"])
    def plume():
        return (
            '<div class="space-y-2">'
            '<h3 class="text-sky-400 font-bold">Helium Plume</h3>'
            '<p class="font-mono text-sm">plume vector locked · null ban active</p></div>'
        )

    @app.route("/quadratic", methods=["GET"])
    @charge_fee(FEE_TABLE["/quadratic"])
    def quadratic():
        return (
            '<div class="space-y-2">'
            '<h3 class="text-violet-400 font-bold">Quadratic Field</h3>'
            '<p class="font-mono text-sm">Q(ψ)=⟨ψ|H|ψ⟩ · φ-harmonic form</p></div>'
        )

    @app.route("/octonion", methods=["GET"])
    @charge_fee(FEE_TABLE["/octonion"])
    def octonion():
        amp = PHI**15
        return (
            '<div class="space-y-2">'
            '<h3 class="text-fuchsia-400 font-bold">8D Manifold</h3>'
            '<div class="grid grid-cols-2 gap-2">'
            '<div class="bg-slate-800/50 p-4 rounded-xl border border-slate-700">'
            '<p class="text-xs text-slate-400">O₁</p>'
            '<p class="text-sm font-mono text-emerald-400">Re(P) ⊗ S¹</p></div>'
            '<div class="bg-slate-800/50 p-4 rounded-xl border border-slate-700">'
            '<p class="text-xs text-slate-400">O₃</p>'
            '<p class="text-sm font-mono text-amber-400">|P| ⊗ S⁷</p></div></div>'
            f'<p class="text-xs font-mono text-slate-400 mt-3">Volume amplification: φ¹⁵ ≈ {amp:.3f}×</p>'
        )

    @app.route("/system/status", methods=["GET"])
    def system_status():
        """Ouroboros Lattice Monitor — auto-refresh HTMX fragment (every 15s)."""
        try:
            mf = ROOT / "HASH_MANIFEST.json"
            manifest = json.loads(mf.read_text()) if mf.exists() else {}
            status_file = ROOT / "symplectic_status.agent.jsonl"
            latest_status = {}
            if status_file.exists():
                lines = status_file.read_text().strip().splitlines()
                if lines:
                    try:
                        latest_status = json.loads(lines[-1])
                    except json.JSONDecodeError:
                        latest_status = {}

            root322 = manifest.get("merkle_root_layer322", "PENDING")
            wasp = manifest.get("wasp_gate_status") or "IDLE"
            ch1700 = (
                manifest.get("channel_1700Q")
                or manifest.get("channel_1700q")
                or "ACKNOWLEDGED"
            )
            harmony = latest_status.get(
                "trappist_harmony_index",
                latest_status.get("harmony_index", "0.7337473231"),
            )
            witness = latest_status.get(
                "entry_index", manifest.get("latest_ledger", "8731")
            )
            coherence = latest_status.get("coherence", 1.0)
            event = latest_status.get("event", "—")

            return f"""
    <div class="space-y-6" hx-get="/system/status" hx-trigger="every 15s" hx-swap="outerHTML">
        <h3 class="text-lg font-bold text-purple-400">Ouroboros Lattice Monitor</h3>
        <div class="grid grid-cols-2 gap-4">
            <div class="bg-slate-800/50 p-4 rounded-xl border border-slate-700">
                <p class="text-xs text-slate-400">Layer 322 Merkle Root</p>
                <p class="text-xs font-mono text-emerald-400 break-all">{root322}</p>
            </div>
            <div class="bg-slate-800/50 p-4 rounded-xl border border-slate-700">
                <p class="text-xs text-slate-400">Strike X Harmony</p>
                <p class="text-xl font-mono text-amber-400">{harmony}</p>
            </div>
            <div class="bg-slate-800/50 p-4 rounded-xl border border-slate-700">
                <p class="text-xs text-slate-400">WASP Gate</p>
                <p class="text-sm font-mono text-blue-400">{wasp}</p>
            </div>
            <div class="bg-slate-800/50 p-4 rounded-xl border border-slate-700">
                <p class="text-xs text-slate-400">1700Q Channel</p>
                <p class="text-sm font-mono text-green-400">{ch1700}</p>
            </div>
        </div>
        <div class="bg-slate-800/30 p-2 rounded-lg border border-slate-700 text-xs font-mono text-slate-400 flex justify-between flex-wrap gap-2">
            <span>Entropy Floor: φ⁻¹⁴¹⁸</span>
            <span>Coherence: {coherence}</span>
            <span>Event: {event}</span>
            <span>Witness Head: {witness}</span>
        </div>
        <p class="text-[10px] text-slate-600 font-mono">hx-trigger=every 15s · free monitor (no Σ fee)</p>
    </div>
    """
        except OSError as e:
            log.exception("system_status IO")
            return _err_html("Monitor unavailable", str(e)), 503
        except Exception as e:
            log.exception("system_status")
            return _err_html("Monitor failed", type(e).__name__), 500

    return app


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    app = try_create_app()
    if app is None:
        print("Flask not installed — vault CLI remains available.")
        print("  python3 -m peqs_vault.credit_vault --demo")
        print("Install: pip install flask eth-account")
        print("FEE_TABLE:", FEE_TABLE)
        print("credit balances:", load_credits().get("balances"))
        return 0
    print("PEQS HTMX Credit Vault on :5000")
    print("FEE_TABLE:", FEE_TABLE)
    app.run(debug=False, port=5000, host="127.0.0.1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
