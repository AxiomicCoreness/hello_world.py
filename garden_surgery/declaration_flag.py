"""HTMX + FastAPI diagnostic for the flagged κ/χ declaration.

Does not rewrite Immutable/self_improvement_trigger.py.
Does not call MCP. Does not print secrets.
"""

from __future__ import annotations

from typing import Any, Dict

from garden_surgery.trigger_excavate import (
    KAPPA_DECLARED,
    diagnostic_scalars,
    golden_hash,
    kappa_decomposition,
)

FLAG = "_DECLARATION_FLAGGED"
EVENT = "/surgery/declaration_flagged_kappa_chi"


def declaration_payload() -> Dict[str, Any]:
    kappa = kappa_decomposition()
    diag = diagnostic_scalars()
    overstated = abs(kappa["phi4_sqrt7"] - KAPPA_DECLARED) > 1e-6
    return {
        "flag": FLAG,
        "event": EVENT,
        "entry": 9024,
        "declaration_overstated": overstated,
        "stated_as_axiom": "kappa_eff = phi^4 * sqrt(7) * chi_Umbral = 12.754",
        "honest_split": {
            "phi4_sqrt7": kappa["phi4_sqrt7"],
            "chi_umbral_fitted": kappa["chi_umbral_fitted"],
            "kappa_declared": KAPPA_DECLARED,
            "chi_is_axiom": False,
        },
        "diagnostic": diag,
        "omega_demo": golden_hash(str(diag["W"])),
        "immutable_file": "Immutable/self_improvement_trigger.py",
        "immutable_rewritten": False,
        "mcp": False,
        "fusion_canonical": 515,
        "hyperion_preserved": 516,
    }


def htmx_fragment() -> str:
    p = declaration_payload()
    h = p["honest_split"]
    d = p["diagnostic"]
    return (
        '<div id="declaration-flag" class="space-y-3">'
        f'<p class="font-mono text-amber-400">{FLAG}</p>'
        f'<p>declaration_overstated: <b>{str(p["declaration_overstated"]).lower()}</b></p>'
        f'<p>φ⁴√7 = {h["phi4_sqrt7"]:.12f}</p>'
        f'<p>χ_Umbral fitted = {h["chi_umbral_fitted"]:.12f} (not an axiom)</p>'
        f'<p>κ declared = {h["kappa_declared"]}</p>'
        f'<p>W = {d["W"]:.3f} · fidelity = {d["fidelity_pct"]:.1f}%</p>'
        f'<p class="text-xs">Ω-demo {p["omega_demo"]} · no MCP · 0516 untouched</p>'
        "</div>"
    )


def build_app():
    """Optional FastAPI app. Import fails only if fastapi is absent."""
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse, JSONResponse

    app = FastAPI(title="Garden declaration flag", version="9024")

    @app.get("/health")
    def health():
        return {"ok": True, "flag": FLAG, "mcp": False}

    @app.get("/diagnostic")
    def diagnostic_json():
        return JSONResponse(declaration_payload())

    @app.get("/diagnostic/htmx", response_class=HTMLResponse)
    def diagnostic_htmx():
        return HTMLResponse(htmx_fragment())

    return app


app = None
try:
    app = build_app()
except ImportError:
    app = None
