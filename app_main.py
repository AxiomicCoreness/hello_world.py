#!/usr/bin/env python3
"""
app_main:app — FastAPI surface with Merkle + Gravastar trigger.

Run:
  uvicorn app_main:app --host 0.0.0.0 --port 8001
  # or dedicated trigger surface:
  uvicorn app_main:app --host 0.0.0.0 --port 8012

Seal: ∀∞φ² · APP_MAIN_MERKLE_8653 · GRAVASTAR_TRIGGER_8654 · SEALED
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from cryptography.merkle import merkle_from_directory

REPO_ROOT = Path(__file__).resolve().parent

app = FastAPI(
    title="Sovereign Garden API",
    version="1.1.0",
    description="POD routes + symplectic Merkle + Gravastar trigger",
)


class MerkleResponse(BaseModel):
    merkle_root: str
    leaf_count: int
    algorithm: str = "sha256"
    root_dir: str
    leaves: List[Dict[str, str]] = Field(default_factory=list)
    seal: str = "∀∞φ² · APP_MAIN_MERKLE_8653 · SEALED"


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "service": "app_main",
        "status": "ok",
        "routes": [
            "/",
            "/health",
            "/status",
            "/symplectic",
            "/merkle/symplectic",
            "/trigger/gravastar",
            "/ports",
        ],
    }


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/status")
def status() -> Dict[str, Any]:
    try:
        from sovereign_engine import PHI, PHASE_LOCK_DEG  # type: ignore

        phi, phase = float(PHI), float(PHASE_LOCK_DEG)
    except Exception:
        phi, phase = 1.618033988749895, 202.6
    try:
        from quantum.gravastar_trigger import STATE

        g = STATE.to_dict()
    except Exception:
        g = {"active": False}
    return {
        "coherence": 1.0,
        "phase_lock_degrees": phase,
        "phi": phi,
        "gravastar_active": g.get("active", False),
        "service": "app_main",
    }


@app.get("/ports")
def ports() -> Dict[str, Any]:
    from quantum.gravastar_trigger import MAPPED_PORTS, TRIGGER_NAME

    return {"trigger": TRIGGER_NAME, "mapped_ports": MAPPED_PORTS}


@app.get("/trigger/gravastar")
@app.post("/trigger/gravastar")
def trigger_gravastar() -> Dict[str, Any]:
    """Trigger_Gravastar_ClarkeYoursaTee — activate on all mapped ports."""
    from quantum.gravastar_trigger import trigger_all

    result = trigger_all()
    # Best-effort notify local metrics registry
    try:
        from prometheus import metrics_server as ms  # type: ignore

        if hasattr(ms, "update_metrics"):
            ms.update_metrics(gravastar_coherence=1.0)
        elif hasattr(ms, "_reg"):
            pass
    except Exception:
        pass
    return result


@app.get("/symplectic")
def symplectic(refresh: bool = Query(False, description="Regenerate before read")) -> Dict[str, Any]:
    status_path = REPO_ROOT / "symplectic_status.json"
    if refresh or not status_path.is_file():
        try:
            import symplectic_status as ss

            aggregate = ss.generate_aggregate_status()
            status_path.write_text(json.dumps(aggregate, indent=2), encoding="utf-8")
            lines = ss.generate_agent_jsonl(aggregate)
            with open(REPO_ROOT / "symplectic_status.agent.jsonl", "w", encoding="utf-8") as f:
                for line in lines:
                    f.write(json.dumps(line) + "\n")
        except Exception as e:
            if not status_path.is_file():
                raise HTTPException(status_code=503, detail=f"symplectic unavailable: {e}") from e
    return json.loads(status_path.read_text(encoding="utf-8"))


@app.get("/merkle/symplectic", response_model=MerkleResponse)
def merkle_symplectic(
    include_leaves: bool = Query(True, description="Include per-file leaf digests"),
) -> MerkleResponse:
    tree = merkle_from_directory(REPO_ROOT)
    if not include_leaves:
        tree = {**tree, "leaves": []}
    return MerkleResponse(
        merkle_root=tree["merkle_root"],
        leaf_count=tree["leaf_count"],
        algorithm=tree["algorithm"],
        root_dir=tree["root_dir"],
        leaves=tree.get("leaves", []),
    )


@app.post("/symplectic/refresh")
def symplectic_refresh() -> Dict[str, Any]:
    data = symplectic(refresh=True)
    tree = merkle_from_directory(REPO_ROOT)
    return {
        "symplectic": data,
        "merkle_root": tree["merkle_root"],
        "leaf_count": tree["leaf_count"],
        "seal": "∀∞φ² · APP_MAIN_MERKLE_8653 · SEALED",
    }


if __name__ == "__main__":
    import os

    import uvicorn

    port = int(os.environ.get("PORT", os.environ.get("GRAVASTAR_PORT", "8012")))
    uvicorn.run("app_main:app", host="0.0.0.0", port=port, reload=False)
