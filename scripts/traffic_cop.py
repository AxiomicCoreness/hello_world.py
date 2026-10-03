#!/usr/bin/env python3
"""Local traffic cop. No external source.

The slot table is copied from .github/workflows/workflow-parity.yml.
This module does not open a socket, does not read the network, and
does not dispatch. It names the one file for a slot.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

FILES = (
    "hypersurface.yml",
    "sovereign-run.yml",
    "ledger-math-framework.yml",
    "sovereign-stack-ci.yml",
    "agent-service-control.yml",
    "ledger-witness-continuity.yml",
    "master-equation-ci.yml",
    "sovereignty-python-package.yml",
    "argo-ci.yml",
    "symplectic-status.yml",
    "catalogue.yml",
    "merge-engine.yml",
    "toolkit-54-exorcise.yml",
    "cd-combinator-argo-rollout.yml",
    "mtls-cert-lifecycle.yml",
    "validate-contract.yml",
    "cd-combinator.yml",
    "multibody-toi.yml",
    "verify-ledger.yml",
    "debug-environment.yml",
    "north-star-witness.yml",
    "witness-chain-contracts.yml",
    "deepseek-cd.yml",
    "oidc-cloud-providers.yml",
    "witness-chain-sqlite.yml",
    "deepseek-ci-secrets.yml",
    "producer-axiom-verify.yml",
    "wood-dragon-dispatch.yml",
    "deepseek-mesh-terminal.yml",
    "pytest.yml",
    "workflow-sync-6cavd.yml",
    "deepseek-ndjson-ci.yml",
    "python-package-ci-correction.yml",
    "workload-smoke.yml",
    "docker-main-image.yml",
    "python-package.yml",
    "dual-ci-venv.yml",
    "quantum_reality_engine_510510.yml",
    "e10-hyperbolic-pytest.yml",
    "restore-deepseek-cd-frozen.yml",
    "e2e-key-check.yml",
    "reward-distribution.yml",
    "eridanus-dual-smoke.yml",
    "scheduled-ci-sweep.yml",
    "garden-surgery.yml",
    "secrets-context-example.yml",
    "generate-frb-bridge.yml",
    "singularity-stream-ci.yml",
    "generate-lock.yml",
    "sovereign-cicd.yml",
    "gravastar-long-horizon.yml",
    "sovereign-core-sidecar.yml",
    "gravastar-mcp-connector.yml",
    "sovereign-engine-final.yml",
    "handover-via-380.yml",
)

N = len(FILES)  # 55


def slot_of(moment: datetime) -> int:
    moment = moment.astimezone(timezone.utc)
    minutes = moment.day * 24 * 60 + moment.hour * 60 + moment.minute
    return (minutes // 15) % N


def route(slot: int) -> dict:
    if not 0 <= slot < N:
        raise ValueError(f"slot out of 0-{N - 1}")
    return {"slot": slot, "file": FILES[slot], "count": 1, "source": "local-table"}


def main(argv: list[str]) -> int:
    if len(argv) == 2:
        slot = int(argv[1])
    else:
        slot = slot_of(datetime.now(timezone.utc))
    print(json.dumps(route(slot)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
