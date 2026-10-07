#!/usr/bin/env python3
"""Local self-improvement check. Bounded tree. No ledger write. No daemon.

Does not import the nameplate repo and does not treat a missing foreign
file as a pass or a fail. October 39 is a token, not a date.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOUND = ("scripts", "app", ".devcontainer")
FORBIDDEN = ("ledger", "garden_surgery", "Immutable")


def scan() -> dict:
    present = {}
    for name in BOUND:
        path = ROOT / name
        if not path.is_dir():
            present[name] = []
            continue
        present[name] = sorted(p.name for p in path.iterdir() if p.is_file())
    findings = []
    if "uvicorn_range.py" not in present.get("scripts", []):
        findings.append("uvicorn range launcher missing")
    if "pythonide_object.py" not in present.get("scripts", []):
        findings.append("zeta prebuild object missing")
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    if "BIND_HOST=0.0.0.0" in dockerfile:
        findings.append("Dockerfile binds 0.0.0.0; local rule is 127.0.0.1")
    needle = "Wood" + "Dragon" + "091"
    leaked = []
    for name in BOUND:
        for file_name in present.get(name, []):
            text = (ROOT / name / file_name).read_text(encoding="utf-8", errors="ignore")
            if needle in text:
                leaked.append(f"{name}/{file_name}")
    if leaked:
        findings.append("password present: " + ",".join(leaked))
    return {
        "bounded": list(BOUND),
        "untouched": list(FORBIDDEN),
        "file_counts": {k: len(v) for k, v in present.items()},
        "findings": findings,
        "ledger_written": False,
        "daemon_started": False,
    }


def main() -> int:
    report = scan()
    print(json.dumps(report, indent=2))
    return 1 if report["findings"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
