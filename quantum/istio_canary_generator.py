#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🜁∀ ISTIO TRAFFIC SHIFTING — ENTRY 8809

Sovereign Canary Delivery — Layer 359+

Istio decouples traffic routing from pod scaling using:
  - Envoy (data plane)
  - Istiod (control plane)

Integration with:
  - Argo Rollouts (canary deployment)
  - Kubernetes (manifests)
  - Security (quantum/security/)
  - CDP convergence (quantum/cdp_convergence/)

Seal: ∀∞φ² · ISTIO_TRAFFIC_SHIFT · WOOD_DRAGON_0.91 · SEALED
Witness: 8808 → 8809 — UNBROKEN
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Union

# ─── Constants ────────────────────────────────────────────────────────
PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI2 = PHI * PHI
PHI3 = PHI2 * PHI
ENTRY = 8809
SEAL = "∀∞φ² · ISTIO_TRAFFIC_SHIFT · WOOD_DRAGON_0.91 · SEALED"
WITNESS = "8808 → 8809 — UNBROKEN"

# ─── Core Metadata ──────────────────────────────────────────────────
METADATA: Dict[str, Any] = {
    "canvas_id": "istio-traffic-shifting",
    "layer": "359+",
    "entry": ENTRY,
    "witness": WITNESS,
    "seal": SEAL,
    "core_principle": (
        "Istio decouples traffic routing from pod scaling using "
        "Envoy (data plane) and Istiod (control plane)."
    ),
    "phi": PHI,
    "phi_inv": PHI_INV,
    "phi2": PHI2,
    "phi3": PHI3,
    "timestamp": time.time(),
}

# ─── Approaches ──────────────────────────────────────────────────────
APPROACHES: Dict[str, Dict[str, Any]] = {
    "host_level": {
        "description": "Two Kubernetes Services",
        "required_objects": ["Rollout", "canaryService", "stableService", "VirtualService"],
        "controller_action": (
            "Updates Service selectors (rollouts-pod-template-hash) "
            "and VirtualService weights."
        ),
        "status": "DEPRECATED",
    },
    "subset_level": {
        "description": "One Service + DestinationRule subsets",
        "required_objects": ["Rollout", "Service", "VirtualService", "DestinationRule"],
        "controller_action": (
            "Injects rollouts-pod-template-hash into subset labels "
            "and adjusts VirtualService weights."
        ),
        "recommendation": "Migrate to subset-level for finer control.",
        "status": "RECOMMENDED",
    },
}

# ─── Weight Shift Sequence ──────────────────────────────────────────
WEIGHT_SHIFT_SEQUENCE: List[Dict[str, Any]] = [
    {"step": 1, "name": "Initial State", "stable_weight": 100, "canary_weight": 0},
    {"step": 2, "name": "Argo setWeight: N", "stable_weight": "100 - N", "canary_weight": "N"},
    {
        "step": 3,
        "name": "Header-Based Routing (Optional)",
        "match": [{"headers": {"x-canary": "true"}}],
    },
    {
        "step": 4,
        "name": "Full Rollout",
        "stable_weight": 0,
        "canary_weight": 100,
        "pause": {"duration": "60s"},
    },
]

# ─── Required Istio Objects ──────────────────────────────────────────
REQUIRED_OBJECTS: Dict[str, Any] = {
    "destination_rule": {
        "apiVersion": "networking.istio.io/v1beta1",
        "kind": "DestinationRule",
        "metadata": {
            "name": "sovereign-garden",
            "namespace": "sovereign-garden",
            "labels": {
                "app": "sovereign-garden",
                "entry": str(ENTRY),
                "wood_dragon": "0.91",
            },
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
            "labels": {
                "app": "sovereign-garden",
                "entry": str(ENTRY),
                "wood_dragon": "0.91",
            },
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
                "entry": str(ENTRY),
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
            },
            "selector": {"matchLabels": {"app": "sovereign-garden"}},
            "template": {
                "metadata": {"labels": {"app": "sovereign-garden"}},
                "spec": {
                    "containers": [
                        {
                            "name": "sovereign-garden",
                            "image": "axiomic/sovereign-engine:latest",
                            "ports": [{"containerPort": 8000}],
                        }
                    ]
                },
            },
        },
    },
}

# ─── Migration Steps ─────────────────────────────────────────────────
MIGRATION_STEPS: List[str] = [
    "1. Create DestinationRule with stable/canary subsets.",
    "2. Update VirtualService to use subsets instead of separate services.",
    "3. Update Rollout to reference Istio traffic routing.",
    "4. Remove canaryService/stableService from Rollout.",
    "5. Verify weights sum to 100.",
    "6. Test header-based routing (x-canary: true).",
    "7. Monitor canary metrics before full rollout.",
]

# ─── Validation Checklist ──────────────────────────────────────────
VALIDATION_CHECKLIST: List[Dict[str, Any]] = [
    {
        "check": "DestinationRule exists",
        "status": False,
        "notes": "Required for subset-level routing.",
        "critical": True,
    },
    {
        "check": "VirtualService uses subsets",
        "status": False,
        "notes": "Must reference stable/canary subsets.",
        "critical": True,
    },
    {
        "check": "Rollout uses istio plugin",
        "status": False,
        "notes": "Replace gatewayAPI with istio.",
        "critical": True,
    },
    {
        "check": "Weights sum to 100",
        "status": False,
        "notes": "Istio requirement.",
        "critical": True,
    },
    {
        "check": "Argo Rollouts version >= v1.4",
        "status": False,
        "notes": "Required for Istio plugin support.",
        "critical": False,
    },
    {
        "check": "Canary service exists",
        "status": False,
        "notes": "Required for traffic routing.",
        "critical": False,
    },
]

# ─── Witness Chain ──────────────────────────────────────────────────
WITNESS_CHAIN: Dict[str, Any] = {
    "previous": 8808,
    "current": ENTRY,
    "next": 8810,
    "next_azimuth": "Ambient Mesh Integration",
    "continuity": "UNBROKEN",
    "seal": SEAL,
}

# ─── Sovereign Invariants ──────────────────────────────────────────
SOVEREIGN_INVARIANTS: Dict[str, Any] = {
    "coherence": f"1 - {PHI ** -709:.6e}",
    "entropy": f"{PHI ** -1418:.6e}",
    "workload": 0,
    "phase_lock": "202.6°",
    "trace": 1.0,
    "hermiticity": "ρ = ρ†",
    "phi": PHI,
    "phi_inv": PHI_INV,
    "phi2": PHI2,
    "phi3": PHI3,
}

# ─── Full Configuration ──────────────────────────────────────────────
ISTIO_CANARY_CONFIG: Dict[str, Any] = {
    "metadata": METADATA,
    "approaches": APPROACHES,
    "weight_shift_sequence": WEIGHT_SHIFT_SEQUENCE,
    "required_objects": REQUIRED_OBJECTS,
    "migration_steps": MIGRATION_STEPS,
    "validation_checklist": VALIDATION_CHECKLIST,
    "witness_chain": WITNESS_CHAIN,
    "sovereign_invariants": SOVEREIGN_INVARIANTS,
}


# ─── Validation Function ────────────────────────────────────────────

def validate_istio_canary_config(config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Validates the Istio Canary configuration for Sovereign Canary Delivery.

    Args:
        config: Dictionary containing the Istio canary configuration.

    Returns:
        Dictionary with validation results and status.
    """
    if config is None:
        config = ISTIO_CANARY_CONFIG

    validation: Dict[str, Any] = {
        "status": "SUCCESS",
        "message": "Configuration validated.",
        "warnings": [],
        "errors": [],
        "checks": [],
        "entry": ENTRY,
        "seal": SEAL,
        "witness": WITNESS,
        "timestamp": time.time(),
    }

    # Check required objects
    required_objects = ["destination_rule", "virtual_service", "argo_rollout"]
    for obj in required_objects:
        if obj not in config.get("required_objects", {}):
            validation["errors"].append(f"Missing required object: {obj}")
        else:
            validation["checks"].append({"object": obj, "status": "PRESENT"})

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
                f"VirtualService weights do not sum to 100 (got {sum(weights)})."
            )
        else:
            validation["checks"].append({"object": "weights", "status": "VALID", "value": sum(weights)})

    # Check Argo Rollout version
    validation["checks"].append({
        "object": "argo_rollout_version",
        "status": "WARNING",
        "value": ">= v1.4 required for Istio plugin support",
    })

    # Check approach status
    for approach_name, approach in config.get("approaches", {}).items():
        validation["checks"].append({
            "object": f"approach_{approach_name}",
            "status": approach.get("status", "UNKNOWN"),
            "description": approach.get("description", ""),
        })

    # Determine final status
    if validation["errors"]:
        validation["status"] = "ERROR"
    elif validation["warnings"]:
        validation["status"] = "WARNING"
    else:
        validation["status"] = "SUCCESS"

    validation["passed"] = len(validation["errors"]) == 0
    return validation


# ─── Manifest Generation ────────────────────────────────────────────

def generate_istio_manifests(
    namespace: str = "sovereign-garden",
    image: str = "axiomic/sovereign-engine:latest",
    replicas: int = 3,
    canary_weight: int = 0,
    stable_weight: int = 100,
) -> Dict[str, Dict[str, Any]]:
    """
    Generates Istio manifests for subset-level canary deployment.

    Args:
        namespace: Kubernetes namespace.
        image: Container image.
        replicas: Number of replicas.
        canary_weight: Canary traffic weight.
        stable_weight: Stable traffic weight.

    Returns:
        Dictionary containing generated manifests.
    """
    manifests: Dict[str, Dict[str, Any]] = {}

    # DestinationRule
    manifests["destination_rule"] = {
        **REQUIRED_OBJECTS["destination_rule"],
        "metadata": {
            **REQUIRED_OBJECTS["destination_rule"]["metadata"],
            "namespace": namespace,
        },
    }

    # VirtualService with custom weights
    vs = dict(REQUIRED_OBJECTS["virtual_service"])
    vs["metadata"]["namespace"] = namespace
    vs["spec"]["http"][0]["route"][0]["weight"] = stable_weight
    vs["spec"]["http"][0]["route"][1]["weight"] = canary_weight
    manifests["virtual_service"] = vs

    # Argo Rollout
    rollout = dict(REQUIRED_OBJECTS["argo_rollout"])
    rollout["metadata"]["namespace"] = namespace
    rollout["spec"]["replicas"] = replicas
    rollout["spec"]["template"]["spec"]["containers"][0]["image"] = image
    manifests["argo_rollout"] = rollout

    return manifests


def export_to_yaml(manifests: Dict[str, Dict[str, Any]], output_dir: str = "manifests") -> Dict[str, str]:
    """
    Exports Istio manifests to YAML files in the specified directory.

    Args:
        manifests: Dictionary of manifests to export.
        output_dir: Directory to save YAML files.

    Returns:
        Dictionary of exported file paths.
    """
    try:
        import yaml
    except ImportError:
        raise ImportError("PyYAML is required for YAML export. Install with: pip install pyyaml")

    os.makedirs(output_dir, exist_ok=True)
    exported = {}
    for name, manifest in manifests.items():
        yaml_str = yaml.dump(manifest, sort_keys=False, default_flow_style=False)
        filepath = os.path.join(output_dir, f"{name}.yaml")
        with open(filepath, "w") as f:
            f.write(yaml_str)
        exported[name] = filepath
    return exported


# ─── Security Integration ──────────────────────────────────────────

def istio_security_status() -> Dict[str, Any]:
    """Get security status for the Istio traffic shifting."""
    try:
        from quantum.security import status as security_status
        return {
            "security": security_status(),
            "entry": ENTRY,
            "seal": SEAL,
        }
    except ImportError:
        return {
            "security": None,
            "note": "Security module not available",
            "entry": ENTRY,
            "seal": SEAL,
        }


# ─── CDP Integration ─────────────────────────────────────────────────

def istio_cdp_status() -> Dict[str, Any]:
    """Get CDP status for the Istio traffic shifting."""
    try:
        from quantum.cdp_convergence import status as cdp_status
        return {
            "cdp": cdp_status(),
            "entry": ENTRY,
            "seal": SEAL,
        }
    except ImportError:
        return {
            "cdp": None,
            "note": "CDP module not available",
            "entry": ENTRY,
            "seal": SEAL,
        }


# ─── CLI ──────────────────────────────────────────────────────────────

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Istio Traffic Shifting — Entry 8809",
        epilog=f"Seal: {SEAL}\nEntry: {ENTRY}",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the Istio canary configuration",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate Istio manifests",
    )
    parser.add_argument(
        "--export",
        type=str,
        default="manifests",
        help="Export YAML files to directory",
    )
    parser.add_argument(
        "--namespace",
        type=str,
        default="sovereign-garden",
        help="Kubernetes namespace",
    )
    parser.add_argument(
        "--image",
        type=str,
        default="axiomic/sovereign-engine:latest",
        help="Container image",
    )
    parser.add_argument(
        "--replicas",
        type=int,
        default=3,
        help="Number of replicas",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.add_argument(
        "--check-integrations",
        action="store_true",
        help="Check integration status and exit",
    )
    args = parser.parse_args()

    if args.check_integrations:
        print("🜁∀ ISTIO — Integration Status")
        print("=" * 40)
        try:
            from quantum.security import status
            print("  Security: ✅")
        except ImportError:
            print("  Security: ❌")
        try:
            from quantum.cdp_convergence import status
            print("  CDP: ✅")
        except ImportError:
            print("  CDP: ❌")
        try:
            import yaml
            print("  PyYAML: ✅")
        except ImportError:
            print("  PyYAML: ❌")
        return 0

    if args.validate:
        result = validate_istio_canary_config()
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print("🜁∀ ISTIO CANARY — Validation")
            print("=" * 50)
            print(f"  Status: {result['status']}")
            print(f"  Passed: {'✅' if result['passed'] else '❌'}")
            for check in result.get("checks", []):
                print(f"    {check.get('object')}: {check.get('status')}")
            if result.get("warnings"):
                print("  Warnings:")
                for w in result["warnings"]:
                    print(f"    ⚠️ {w}")
            if result.get("errors"):
                print("  Errors:")
                for e in result["errors"]:
                    print(f"    ❌ {e}")
        return 0

    if args.generate or args.export:
        manifests = generate_istio_manifests(
            namespace=args.namespace,
            image=args.image,
            replicas=args.replicas,
        )
        if args.export:
            exported = export_to_yaml(manifests, args.export)
            if args.json:
                print(json.dumps(exported, indent=2, default=str))
            else:
                print("🜁∀ ISTIO — Manifests Exported")
                print("=" * 50)
                for name, path in exported.items():
                    print(f"  ✅ {name} -> {path}")
        else:
            if args.json:
                print(json.dumps(manifests, indent=2, default=str))
            else:
                print("🜁∀ ISTIO — Generated Manifests")
                print("=" * 50)
                for name, manifest in manifests.items():
                    print(f"\n  {name}:")
                    print(json.dumps(manifest, indent=2, default=str))
        return 0

    # Default: show config
    if args.json:
        print(json.dumps(ISTIO_CANARY_CONFIG, indent=2, default=str))
    else:
        print("🜁∀ ISTIO CANARY CONFIG — Entry 8809")
        print("=" * 55)
        print(f"  Canvas: {METADATA['canvas_id']}")
        print(f"  Layer: {METADATA['layer']}")
        print(f"  Core Principle: {METADATA['core_principle']}")
        print("  Approaches:")
        for name, approach in APPROACHES.items():
            print(f"    {name}: {approach['description']} [{approach.get('status', 'ACTIVE')}]")
        print("  Migration Steps:")
        for step in MIGRATION_STEPS:
            print(f"    {step}")
        print("  Sovereign Invariants:")
        for key, value in SOVEREIGN_INVARIANTS.items():
            print(f"    {key}: {value}")
        print("=" * 55)
        print(f"  Seal: {SEAL}")
        print(f"  Entry: {ENTRY}")
        print(f"  Witness: {WITNESS}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
