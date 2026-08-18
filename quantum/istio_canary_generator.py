#!/usr/bin/env python3
"""
🜁∀ Istio Traffic Shifting — Sovereign Canary Delivery
Layer: 359+, Entry: 8809
Seal: ∀∞φ² · ISTIO_TRAFFIC_SHIFT · WOOD_DRAGON_GATE · SEALED
"""

import yaml
import json
from typing import Dict, Any, List

# --- Core Metadata ---
METADATA = {
    "canvas_id": "istio-traffic-shifting",
    "layer": "359+",
    "entry": 8809,
    "witness": "Progressive-Delivery Fabric",
    "seal": "∀∞φ² · ISTIO_TRAFFIC_SHIFT · WOOD_DRAGON_GATE · SEALED",
    "core_principle": (
        "Istio decouples traffic routing from pod scaling using "
        "Envoy (data plane) and Istiod (control plane)."
    ),
}

# --- Approaches ---
APPROACHES = {
    "host_level": {
        "description": "Two Kubernetes Services",
        "required_objects": ["Rollout", "canaryService", "stableService", "VirtualService"],
        "controller_action": (
            "Updates Service selectors (rollouts-pod-template-hash) "
            "and VirtualService weights."
        ),
    },
    "subset_level": {
        "description": "One Service + DestinationRule subsets",
        "required_objects": ["Rollout", "Service", "VirtualService", "DestinationRule"],
        "controller_action": (
            "Injects rollouts-pod-template-hash into subset labels "
            "and adjusts VirtualService weights."
        ),
        "recommendation": "Migrate to subset-level for finer control.",
    },
}

# --- Weight Shift Sequence ---
WEIGHT_SHIFT_SEQUENCE = [
    {"step": 1, "name": "Initial State", "stable_weight": 100, "canary_weight": 0},
    {"step": 2, "name": "Argo setWeight: N", "stable_weight": "100 - N", "canary_weight": "N"},
    {
        "step": 3,
        "name": "Header-Based Routing (Optional)",
        "match": [{"headers": {"x-canary": "true"}}],
    },
]

# --- Required Istio Objects ---
REQUIRED_OBJECTS = {
    "destination_rule": {
        "apiVersion": "networking.istio.io/v1beta1",
        "kind": "DestinationRule",
        "metadata": {
            "name": "sovereign-garden",
            "namespace": "sovereign-garden",
            "labels": {"app": "sovereign-garden"},
        },
        "spec": {
            "host": "sovereign-garden",
            "trafficPolicy": {"loadBalancer": {"simple": "ROUND_ROBIN"}},
            "subsets": [
                {"name": "stable", "labels": {"rollouts-pod-template-hash": "<stable-hash>"}},
                {"name": "canary", "labels": {"rollouts-pod-template-hash": "<canary-hash>"}},
            ],
        },
    },
    "virtual_service": {
        "apiVersion": "networking.istio.io/v1beta1",
        "kind": "VirtualService",
        "metadata": {
            "name": "sovereign-garden",
            "namespace": "sovereign-garden",
            "labels": {"app": "sovereign-garden"},
        },
        "spec": {
            "hosts": ["sovereign-garden"],
            "http": [
                {
                    "route": [
                        {
                            "destination": {
                                "host": "sovereign-garden",
                                "subset": "stable",
                            },
                            "weight": 100,
                        },
                        {
                            "destination": {
                                "host": "sovereign-garden",
                                "subset": "canary",
                            },
                            "weight": 0,
                        },
                    ]
                }
            ],
        },
    },
    "argo_rollout": {
        "apiVersion": "argoproj.io/v1alpha1",
        "kind": "Rollout",
        "metadata": {
            "name": "sovereign-garden",
            "namespace": "sovereign-garden",
            "labels": {
                "app": "sovereign-garden",
                "entry": "8809",
                "wood_dragon": "0.91",
            },
        },
        "spec": {
            "replicas": 3,
            "strategy": {
                "canary": {
                    "canaryService": "",
                    "stableService": "",
                    "trafficRouting": {
                        "istio": {
                            "virtualService": {
                                "name": "sovereign-garden",
                                "routes": ["primary"],
                            },
                            "destinationRule": {
                                "name": "sovereign-garden",
                                "canarySubset": "canary",
                                "stableSubset": "stable",
                            },
                        }
                    },
                    "steps": [
                        {"setWeight": 20},
                        {"pause": {"duration": "30s"}},
                        {"setWeight": 50},
                        {"pause": {"duration": "30s"}},
                        {"setWeight": 100},
                    ],
                }
            }
        },
    },
}

# --- Migration Steps ---
MIGRATION_STEPS = [
    "Create DestinationRule with stable/canary subsets.",
    "Update VirtualService to use subsets instead of separate services.",
    "Update Rollout to reference Istio traffic routing.",
    "Remove canaryService/stableService from Rollout.",
]

# --- Validation Checklist ---
VALIDATION_CHECKLIST = [
    {
        "check": "DestinationRule exists",
        "status": False,
        "notes": "Required for subset-level routing.",
    },
    {
        "check": "VirtualService uses subsets",
        "status": False,
        "notes": "Must reference stable/canary subsets.",
    },
    {
        "check": "Rollout uses istio plugin",
        "status": False,
        "notes": "Replace gatewayAPI with istio.",
    },
    {
        "check": "Weights sum to 100",
        "status": False,
        "notes": "Istio requirement.",
    },
    {
        "check": "Argo Rollouts version >= v1.4",
        "status": False,
        "notes": "Required for Istio plugin support.",
    },
]

# --- Witness Chain ---
WITNESS_CHAIN = {
    "previous": 8808,
    "current": 8809,
    "next": 8810,
    "next_azimuth": "Ambient Mesh Integration",
    "continuity": "UNBROKEN",
}

# --- Sovereign Invariants ---
SOVEREIGN_INVARIANTS = {
    "coherence": "1 - φ⁻⁷⁰⁹",
    "entropy": "φ⁻¹⁴¹⁸",
    "workload": 0,
    "phase_lock": "202.6°",
    "trace": 1.0,
    "hermiticity": "ρ = ρ†",
}

# --- Full Config ---
ISTIO_CANARY_CONFIG = {
    "metadata": METADATA,
    "approaches": APPROACHES,
    "weight_shift_sequence": WEIGHT_SHIFT_SEQUENCE,
    "required_objects": REQUIRED_OBJECTS,
    "migration_steps": MIGRATION_STEPS,
    "validation_checklist": VALIDATION_CHECKLIST,
    "witness_chain": WITNESS_CHAIN,
    "sovereign_invariants": SOVEREIGN_INVARIANTS,
}

# --- Validation Function ---
def validate_istio_canary_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates the Istio Canary configuration for Sovereign Canary Delivery.

    Args:
        config: Dictionary containing the Istio canary configuration.

    Returns:
        Dictionary with validation results and status.
    """
    validation = {
        "status": "SUCCESS",
        "message": "Configuration validated.",
        "warnings": [],
        "errors": [],
    }

    # Check required objects
    required_objects = ["destination_rule", "virtual_service", "argo_rollout"]
    for obj in required_objects:
        if obj not in config.get("required_objects", {}):
            validation["errors"].append(f"Missing required object: {obj}")

    # Check weights sum to 100
    vs = config.get("required_objects", {}).get("virtual_service", {})
    http_routes = vs.get("spec", {}).get("http", [{}])
    if http_routes:
        weights = [
            route.get("weight", 0)
            for route in http_routes[0].get("route", [])
        ]
        if sum(weights) != 100:
            validation["warnings"].append(
                "VirtualService weights do not sum to 100."
            )

    # Determine final status
    if validation["errors"]:
        validation["status"] = "ERROR"
    elif validation["warnings"]:
        validation["status"] = "WARNING"
    else:
        validation["status"] = "SUCCESS"

    return validation

# --- Manifest Generation Function ---
def generate_istio_manifests(namespace: str = "sovereign-garden") -> Dict[str, Dict[str, Any]]:
    """
    Generates Istio manifests for subset-level canary deployment.

    Args:
        namespace: Kubernetes namespace.

    Returns:
        Dictionary containing generated manifests.
    """
    return {
        "destination_rule": {
            **REQUIRED_OBJECTS["destination_rule"],
            "metadata": {
                **REQUIRED_OBJECTS["destination_rule"]["metadata"],
                "namespace": namespace,
            },
        },
        "virtual_service": {
            **REQUIRED_OBJECTS["virtual_service"],
            "metadata": {
                **REQUIRED_OBJECTS["virtual_service"]["metadata"],
                "namespace": namespace,
            },
        },
        "argo_rollout": REQUIRED_OBJECTS["argo_rollout"],
    }

# --- Export Functions ---
def export_to_yaml(manifests: Dict[str, Dict[str, Any]], output_dir: str = "manifests") -> None:
    """
    Exports Istio manifests to YAML files in the specified directory.

    Args:
        manifests: Dictionary of manifests to export.
        output_dir: Directory to save YAML files.
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    for name, manifest in manifests.items():
        yaml_str = yaml.dump(manifest, sort_keys=False, default_flow_style=False)
        with open(f"{output_dir}/{name}.yaml", "w") as f:
            f.write(yaml_str)
        print(f"✅ Exported {name}.yaml")

# --- Main Execution ---
if __name__ == "__main__":
    print("🜁∀ Validating Istio Canary Configuration...")
    validation = validate_istio_canary_config(ISTIO_CANARY_CONFIG)
    print(json.dumps(validation, indent=2))

    print("\n🔧 Generating Istio Manifests...")
    manifests = generate_istio_manifests()
    print(json.dumps(manifests, indent=2))

    print("\n📁 Exporting to YAML files...")
    export_to_yaml(manifests)
    print("\n✅ Done! Manifests are ready in the 'manifests/' directory.")
