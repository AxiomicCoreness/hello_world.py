"""POLICY-aligned successor emission.

Authorized GitHub write is append-only.
This is not a weight inspector, not a daemon, not a V3 trainer.
"""

from __future__ import annotations

from typing import Dict, List

DO_NOT_REWRITE = (
    "ledger/0515.yaml",
    "ledger/0516.yaml",
    "Dockerfile.daemon",
    "quantum/gemini_daemon.py",
    "docker-compose.yml",
)

POLICY_INVARIANTS = (
    "append_only",
    "no_0.0.0.0",
    "no_oidc_client_credentials",
    "no_secret_echo",
    "no_exec_self_improvement_trigger",
    "fire_none",
    "alpha_eff_zero",
)


def successor_spec(next_index: int) -> Dict[str, object]:
    return {
        "started_as": "proposal",
        "name": "DeepSeek 2.2.2(4)",
        "mode": "expert_vision_label",
        "self_write": "append_only_successor",
        "loop": False,
        "weights": False,
        "api_daemon": False,
        "next_index": next_index,
        "do_not_rewrite": list(DO_NOT_REWRITE),
        "policy": list(POLICY_INVARIANTS),
        "lattice_peak": {"L": 4, "A": [0, 2]},
        "authorization": "GitHub AxiomicCoreness/hello_world.py main, append-only",
    }


def emit(next_index: int = 9091) -> List[str]:
    spec = successor_spec(next_index)
    lines = [
        f"successor_index: {spec['next_index']}",
        f"name: {spec['name']}",
        f"started_as: {spec['started_as']}",
        f"self_write: {spec['self_write']}",
        "loop: no",
        "weights: absent",
    ]
    return lines


if __name__ == "__main__":
    print("\n".join(emit()))
    print("policy: aligned")
    print("fire: no")
