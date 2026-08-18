#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EM-006 / SIMD-001 — dispatch loop with Merkle root + OIDC handover feedback
===========================================================================
1. Soak-validate SIMD state (φ³ × 3 epochs)
2. Package payload (ports, WASP 753/759, pending=6 handshake analogy)
3. Merkle-root the canonical JSON (SHA-256 leaves, full 64-hex, no truncation)
4. Mint/verify OIDC handover tokens (orchestrator · worker · grafana · prometheus · simd)
5. Write dispatch artifact for CronJob / CI metric scrape

Seal: ∀∞φ² · SIMD_DISPATCH_MERKLE_OIDC_8678 · SEALED
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, List

from quantum.batch_simd_tuning import (
    OPEN_PORTS,
    TRACE_FIXED,
    open_porting_information,
    soak,
    tune,
)


def _leaf(path: str, content: bytes) -> str:
    h = hashlib.sha256()
    h.update(path.encode("utf-8"))
    h.update(b"\0")
    h.update(content)
    return h.hexdigest()  # full 64


def merkle_root(blobs: Dict[str, bytes]) -> str:
    """Binary Merkle over sorted path-qualified leaves; full digests only."""
    if not blobs:
        return hashlib.sha256(b"empty").hexdigest()
    level: List[str] = [_leaf(k, blobs[k]) for k in sorted(blobs.keys())]
    while len(level) > 1:
        nxt: List[str] = []
        for i in range(0, len(level), 2):
            if i + 1 < len(level):
                pair = (level[i] + level[i + 1]).encode()
            else:
                pair = (level[i] + level[i]).encode()
            nxt.append(hashlib.sha256(pair).hexdigest())
        level = nxt
    return level[0]


def oidc_handover_feedback() -> Dict[str, Any]:
    try:
        from batch_oidc_tokenizer import batch_mint, verify_token

        tokens = batch_mint(
            [
                "orchestrator",
                "clarke_yoursa_tee_worker",
                "grafana",
                "prometheus",
                "simd_em006",
            ],
            ttl_s=3600,
        )
        verified = []
        for t in tokens:
            v = verify_token(t["token"])
            verified.append(
                {
                    "sub": t["payload"]["sub"],
                    "ok": bool(v.get("ok")),
                    "secret_len": t["secret_len"],
                    "sig_len": len(t["sig"]),  # must be 64
                }
            )
        return {
            "ok": all(x["ok"] for x in verified),
            "subjects": verified,
            "policy": "full_64_char_no_truncation",
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "policy": "full_64_char_no_truncation"}


def build_payload() -> Dict[str, Any]:
    soak_report = soak(epochs=3)
    state = soak_report["last"] if soak_report.get("last") else tune()
    ports = open_porting_information()
    oidc = oidc_handover_feedback()

    body = {
        "protocol": "EM-006/SIMD-001",
        "event": "/workload_dispatch_em006_merkle_oidc",
        "simd_initial_condition": state,
        "soak": {
            "pass": soak_report.get("pass"),
            "traces": soak_report.get("traces"),
            "epochs": soak_report.get("soak_epochs", 3),
        },
        "port_routing": {
            "prometheus_scrape": 9090,
            "simd_metrics": 9095,
            "wasp_callback": 8012,
            "ouroboros_feedback_ingest": 8001,
            "worker": 8000,
            "hyperian": 8080,
        },
        "ports_full": ports["ports"],
        "workload_dispatch": {
            "target": "WASP-107b",
            "pending_entries": 6,  # handshake analogy φ³…φ⁶ + charge + fire
            "action": "flush_and_seal",
            "post_dispatch": "trigger_cronjob_solar_gate_convergence",
            "repo_window": {"anchor": 753, "listen": 759},
        },
        "oidc_handover_feedback": oidc,
        "ci_cron_hooks": {
            "symplectic_status_cron": "0 */6 * * *",
            "solar_gate_convergence": "0 */6 * * *",
            "metrics_to_watch": [
                "trappist_choir_coherence",
                "trappist_harmony_index",
                "worker_pauli_trace",
                "worker_systems_go",
                "soul_cannon_charge_joules",
            ],
        },
        "timestamp": time.time(),
        "seal": "∀∞φ² · SIMD_DISPATCH_MERKLE_OIDC_8678 · SEALED",
    }

    # Merkle over canonical sections (full digests)
    blobs = {
        "simd": json.dumps(state, sort_keys=True, separators=(",", ":")).encode(),
        "soak": json.dumps(body["soak"], sort_keys=True, separators=(",", ":")).encode(),
        "ports": json.dumps(body["port_routing"], sort_keys=True, separators=(",", ":")).encode(),
        "oidc": json.dumps(
            {"ok": oidc.get("ok"), "subjects": [s.get("sub") for s in oidc.get("subjects", [])]},
            sort_keys=True,
            separators=(",", ":"),
        ).encode(),
    }
    root = merkle_root(blobs)
    assert len(root) == 64, "Merkle root must be full 64-hex"
    body["merkle"] = {
        "algorithm": "sha256-path-qualified",
        "root": root,
        "leaf_count": len(blobs),
        "truncate": False,
    }
    body["feedback_loop"] = {
        "mode": "eternal",
        "initial_condition": "soak_validated_simd",
        "merkle_root": root,
        "oidc_ok": bool(oidc.get("ok")),
    }
    return body


def dispatch(out: str = "/tmp/em006_simd001_dispatch.json") -> Dict[str, Any]:
    payload = build_payload()
    path = Path(out)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    payload["written"] = str(path)
    return payload


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/tmp/em006_simd001_dispatch.json")
    args = ap.parse_args()
    p = dispatch(args.out)
    print(f"soak_pass={p['soak']['pass']} merkle={p['merkle']['root']}")
    print(f"oidc_ok={p['oidc_handover_feedback'].get('ok')} written={p['written']}")
    print(f"pending_entries={p['workload_dispatch']['pending_entries']} target={p['workload_dispatch']['target']}")


if __name__ == "__main__":
    main()
