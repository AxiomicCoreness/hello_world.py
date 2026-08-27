"""HTMX + FastAPI diagnostic. Does not rewrite Immutable/. Does not print secrets."""

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
        "honest_split": {
            "phi4_sqrt7": kappa["phi4_sqrt7"],
            "chi_umbral_fitted": kappa["chi_umbral_fitted"],
            "kappa_declared": KAPPA_DECLARED,
            "chi_is_axiom": False,
        },
        "diagnostic": diag,
        "omega_demo": golden_hash(str(diag["W"])),
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
        '<div id="declaration-flag">'
        f'<p>{FLAG}</p>'
        f'<p>overstated: {str(p["declaration_overstated"]).lower()}</p>'
        f'<p>W = {d["W"]:.3f}</p>'
        "</div>"
    )


def build_app():
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse, JSONResponse

    app = FastAPI(title="Garden declaration flag", version="9031")

    @app.middleware("http")
    async def garden_headers(request, call_next):
        from garden_surgery.anomaly_distance import response_headers
        response = await call_next(request)
        for k, v in response_headers().items():
            response.headers[k] = v
        return response

    @app.get("/health")
    def health():
        return {"ok": True, "flag": FLAG, "mcp": False, "tree": "9031", "qed": True}

    @app.get("/diagnostic")
    def diagnostic_json():
        return JSONResponse(declaration_payload())

    @app.get("/diagnostic/htmx", response_class=HTMLResponse)
    def diagnostic_htmx():
        return HTMLResponse(htmx_fragment())

    @app.get("/workers/tree")
    def workers_tree():
        from garden_surgery.worker_tree import tree_payload
        return JSONResponse(tree_payload())

    @app.get("/workers/{worker_id}")
    def worker_node(worker_id: str):
        from garden_surgery.worker_tree import children_of, lineage, node, parent_of, siblings_of
        n = node(worker_id)
        if n is None:
            return JSONResponse({"ok": False, "id": worker_id}, status_code=404)
        return JSONResponse({"ok": True, "node": n, "parent": parent_of(worker_id), "siblings": siblings_of(worker_id), "children": children_of(worker_id), "lineage": lineage(worker_id)})

    @app.get("/anomaly")
    def anomaly_json():
        from garden_surgery.anomaly_distance import payload as anomaly_payload
        return JSONResponse(anomaly_payload())

    @app.get("/anomaly/math")
    def anomaly_math():
        from garden_surgery.anomaly_distance import math_form
        return JSONResponse(math_form())

    @app.get("/override")
    def override_json():
        from garden_surgery.anomaly_distance import override_payload
        return JSONResponse(override_payload())

    return app

app = None
try:
    app = build_app()
except ImportError:
    app = None
