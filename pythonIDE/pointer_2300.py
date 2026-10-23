#!/usr/bin/env python3
"""Clarke Yoursa Tee

Pointer 2300 — Context Layer 314 wire.

Names (does not invent) the Layer 314 cryptographic anchors and the TeaVM /
HHMI / K8s surfaces they bind to. Digests are full 64-hex; never truncate.
Hard policies: append-only ledger, full digests, float safety via math.isclose.

Pattern sibling: pythonIDE/g1_integration_pointer.py
Anchor module:   quantum/radar_lindblad/layer314_anchor.py
"""

from __future__ import annotations

import json
import math
from typing import Any, Dict

AUTHOR = "Clarke Yoursa Tee"
POINTER_ID = 2300
CONTEXT_LAYER = 314

# Full SHA-256 hex — Context Layer 314 (see quantum/radar_lindblad/layer314_anchor.py
# and quantum/sovereign_lattice_constants_8745.py). Do not shorten.
ANCHOR = "8a250cf445e8ad0cc8d06d0096b969029a175a14eb58838e734f1975358b860d"
LEAF = "807de931c86add23baabafd1252dcc89cbcc23812be1f69e8fc215e51849ee68"
DOMAIN = "GARDEN.LAYER314.ANCHOR.v1"

HARD_POLICIES = {
    "append_only": True,
    "full_digests": True,
    "float_compare": "math.isclose",
    "digest_hex_len": 64,
    "no_truncation": True,
}

# How 2300 points: each key is a role; value is the path (or path:note) on main.
LOCATIONS = {
    "layer314_anchor_module": "quantum/radar_lindblad/layer314_anchor.py",
    "layer314_shim": "quantum/layer314_anchor.py",
    "layer314_constants": "quantum/sovereign_lattice_constants_8745.py",
    "layer314_context": "quantum/radar_lindblad/context.md",
    "teavm_rhythm": "games/teavm-rhythm/",
    "teavm_pom": "games/teavm-rhythm/pom.xml",
    "hhmi_skill": "skills/hhmi/",
    "hhmi_context": "skills/hhmi/assets/context.json",
    "hhmi_map": "skills/hhmi/assets/HHMIJaneliaMap.xml",
    "hhmi_connectome_loader": "src/main/java/com/fruitfly/brain/ConnectomeLoader.java",
    "hhmi_connectome_loader_skill_copy": "skills/hhmi/java/src/main/java/com/fruitfly/brain/ConnectomeLoader.java",
    "k8s_ingress_layer314": "k8s/ingress.yaml",
    "k8s_service_port380": "k8s/service-port-380.yaml",
    "k8s_deployment_port380": "k8s/deployment-port-380.yaml",
    "k8s_install": "quantum/install_k8s.sh",
    "port380_gate": "quantum/radar_lindblad/port_380_gate.py",
    "pointer_history": "docs/pointer-history.md",
    "float_safety_kernel": "wired_kernel.py",
}


def pointer_payload() -> Dict[str, Any]:
    assert len(ANCHOR) == 64 and len(LEAF) == 64
    phi = (1.0 + math.sqrt(5.0)) / 2.0
    return {
        "author": AUTHOR,
        "pointer_id": POINTER_ID,
        "context_layer": CONTEXT_LAYER,
        "domain": DOMAIN,
        "anchors": {
            "anchor": ANCHOR,
            "leaf": LEAF,
        },
        "hard_policies": HARD_POLICIES,
        "phi_check": {
            "phi": phi,
            "phi2_is_phi_plus_1": math.isclose(phi * phi, phi + 1.0, rel_tol=0.0, abs_tol=1e-15),
        },
        "locations": LOCATIONS,
        "points_how": (
            f"pointer {POINTER_ID} → Context Layer {CONTEXT_LAYER} "
            f"Anchor={ANCHOR} Leaf={LEAF} via "
            f"{LOCATIONS['layer314_anchor_module']}; surfaces TeaVM/HHMI/K8s as listed"
        ),
    }


def main() -> None:
    print(json.dumps(pointer_payload(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
