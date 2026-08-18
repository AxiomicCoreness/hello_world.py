#!/usr/bin/env python3
"""argo_rollout_setup.py – Apply Argo Rollout and AnalysisTemplate."""
import subprocess
from pathlib import Path

MANIFESTS = [
    "argocd/analysis-health.yaml",
    "argocd/rollout-sovereign-garden.yaml",
]

def apply_manifests():
    for m in MANIFESTS:
        p = Path(m)
        if p.exists():
            subprocess.run(
                ["kubectl", "apply", "-f", str(p), "-n", "sovereign-garden"],
                check=True,
            )
            print(f"Applied {m}")
        else:
            print(f"Warning: {m} not found")

if __name__ == "__main__":
    apply_manifests()
