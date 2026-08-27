"""garden_surgery — append-only diffusion of the Garden monolith.

Does not replace core/, sovereign_engine.py, or sealed ledger bodies.
Run:  PYTHONPATH=. python3 -m garden_surgery
"""

from garden_surgery.theorems import TheoremReport, check_theorems
from garden_surgery.environment import EnvReport, probe_environment
from garden_surgery.surfaces import SurfaceReport, probe_surfaces

__all__ = [
    "TheoremReport",
    "EnvReport",
    "SurfaceReport",
    "check_theorems",
    "probe_environment",
    "probe_surfaces",
    "diagnose",
]


def diagnose(repo_root=None):
    """One-shot interoperability diagnosis. Never prints secret values."""
    return {
        "theorems": check_theorems().as_dict(),
        "environment": probe_environment().as_dict(),
        "surfaces": probe_surfaces(repo_root=repo_root).as_dict(),
    }
