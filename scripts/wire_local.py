#!/usr/bin/env python3
"""Local wire of files that exist in this session. Missing stages are reported, not invented."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UNITREE = ROOT / "unitree"
STAGES = [
    ("compile-stub", [sys.executable, "-m", "py_compile", str(ROOT / "garden_surgery" / "sovereign_automaton_10_06.py")]),
    ("path-map", [sys.executable, str(UNITREE / "scripts" / "archive_path_map.py")]),
    ("torch-guard", [sys.executable, str(UNITREE / "scripts" / "pytorch_cpu_guard.py")]),
    ("hexstrike", [sys.executable, str(UNITREE / "scripts" / "hexstrike.py"), str(ROOT / "fixtures" / "ledger")]),
    ("metrics-chart", [sys.executable, str(UNITREE / "scripts" / "metrics_chart.py"), str(ROOT / "fixtures" / "metrics.json"), str(ROOT / "fixtures" / "metrics.svg")]),
    ("torch-metrics", [sys.executable, str(UNITREE / "scripts" / "pytorch_metrics.py"), str(ROOT / "fixtures" / "metrics.json")]),
]
MISSING = (
    "scripts/ast_guard.py",
    "scripts/cdp_status.py",
    "scripts/traffic_cop.py",
    "kernel/method_catalogue_loop.py",
    "k8s/cronjob-hexstrike.yaml",
)


def main() -> int:
    rows = []
    failed = 0
    for name, cmd in STAGES:
        target = next((Path(part) for part in reversed(cmd) if part.endswith(".py")), None)
        if target is not None and not target.exists():
            rows.append({"stage": name, "status": "missing-script", "path": str(target)})
            failed += 1
            continue
        proc = subprocess.run(cmd, capture_output=True, text=True)
        rows.append({
            "stage": name,
            "status": "ok" if proc.returncode == 0 else "fail",
            "code": proc.returncode,
            "tail": (proc.stdout or proc.stderr)[-240:],
        })
        if proc.returncode != 0:
            failed += 1
    report = {
        "wired": rows,
        "not_on_disk": [item for item in MISSING if not (ROOT / item).exists()],
    }
    print(json.dumps(report, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
