#!/usr/bin/env python3
"""
First SIMD packet handshake.
Local only. Does not call kubectl.
Generates the packet, seals it with SHA3-256, and logs to ledger.v2/.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

PACKET = {
    "packet": 1,
    "layout": "simd-batch-step",
    "manifest": "k8s/cronjob-simd-step.yaml",
    "deploy": "kubectl apply -f k8s/cronjob-simd-step.yaml -n seagate-mimic",
    "argo_path": "argocd",
    "argo_syncs_cronjob": False,
    "schedule": "0 */6 * * *",
    "concurrencyPolicy": "Forbid",
    "phase_deg": 202.6,
    "zeta_bound": 4.3227,  # CORRECTED: from 2.366 (stale) to 4.3227 (canonical formula)
    "sent": True,
}

def main() -> int:
    # 1. Serialize the packet canonically (sorted keys, compact separators)
    canon = json.dumps(PACKET, sort_keys=True, separators=(",", ":"))
    
    # 2. Compute the SHA3-256 seal
    seal_hash = hashlib.sha3_256(canon.encode("utf-8")).hexdigest()
    
    # 3. Attach the seal to the output record
    record = {
        "seal_algo": "sha3_256",
        "seal_hex": seal_hash,
        "packet": PACKET
    }
    
    # 4. Write to the new ledger.v2 directory
    ledger_dir = Path("ledger.v2")
    ledger_dir.mkdir(exist_ok=True)
    path = ledger_dir / "simd_first_packet.jsonl"
    
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
        
    print(json.dumps(record, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
