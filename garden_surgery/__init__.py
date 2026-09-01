"""
garden_surgery — append-only diffusion of the Garden monolith.

Does not replace core/, sovereign_engine.py, or sealed ledger bodies.
Run:  PYTHONPATH=. python3 -m garden_surgery
"""

from garden_surgery.theorems import TheoremReport, check_theorems
from garden_surgery.environment import EnvReport, probe_environment
from garden_surgery.surfaces import SurfaceReport, probe_surfaces
from garden_surgery.trigger_excavate import (
    KAPPA_DECLARED,
    diagnostic_scalars,
    golden_hash,
    kappa_decomposition,
)
from garden_surgery.anomaly_distance import payload as anomaly_payload, math_form, override_payload, response_headers
from garden_surgery.worker_tree import tree_payload, node, parent_of, siblings_of, children_of, lineage
from garden_surgery.excavate_immutable import excavate, ExcavateReport, golden_hash as excavate_golden_hash

__all__ = [
    "TheoremReport",
    "EnvReport",
    "SurfaceReport",
    "check_theorems",
    "probe_environment",
    "probe_surfaces",
    "diagnose",
    "KAPPA_DECLARED",
    "diagnostic_scalars",
    "golden_hash",
    "kappa_decomposition",
    "anomaly_payload",
    "math_form",
    "override_payload",
    "response_headers",
    "tree_payload",
    "node",
    "parent_of",
    "siblings_of",
    "children_of",
    "lineage",
    "excavate",
    "ExcavateReport",
    "excavate_golden_hash",
]


def diagnose(repo_root=None):
    """One-shot interoperability diagnosis. Never prints secret values."""
    return {
        "theorems": check_theorems().as_dict(),
        "environment": probe_environment().as_dict(),
        "surfaces": probe_surfaces(repo_root=repo_root).as_dict(),
    }
