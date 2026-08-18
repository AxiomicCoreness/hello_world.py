#!/usr/bin/env python3
"""
apply_gateway_route.py
Apply Gateway API manifests for stable/canary traffic splitting.
Pure PythonIDE fallback using kubectl subprocess.
"""

import subprocess
from pathlib import Path

MANIFESTS = [
    "argocd/sovereign-garden-stable.yaml",
    "argocd/sovereign-garden-canary.yaml",
    "argocd/sovereign-garden-httproute.yaml",
]

NAMESPACE = "sovereign-garden"

def apply_all():
    for manifest in MANIFESTS:
        path = Path(manifest)
        if not path.exists():
            print(f"⚠️  Missing {manifest}")
            continue
        cmd = [
            "kubectl", "apply",
            "-f", str(path),
            "-n", NAMESPACE,
        ]
        subprocess.run(cmd, check=True)
        print(f"✅ Applied {manifest}")

if __name__ == "__main__":
    apply_all()
