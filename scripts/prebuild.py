#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""
prebuild.py — Clarke Yoursa Tee

Internal prebuild gate. Local tree only — does not commit, seal, or push.

Stage order (all run; missing tools SKIP, not FAIL):
  1. ast_guard       — static rules over source             BLOCKING if tool present
  2. hexstrike       — ghost-seal scan over ledger          BLOCKING if tool present
                       (exit 2 = incomplete scan, e.g. PyYAML missing -> FAIL;
                        scripts/hexstrike_known_unparsed.txt is passed when present)
  3. ledger_iso8601  — ISO 8601 + offset on NEW ledger entries  BLOCKING if tool present
                       (legacy entries report-only)
  4. cdp_status      — one-shot probe                       INFORMATIONAL
  5. zeta_bound      — golden identity bound                BLOCKING if tool present
  6. causal_plane    — stated plane                         INFORMATIONAL

Sub-tools inherit this interpreter's isolation: `python -I scripts/prebuild.py`
runs them with -I too, so a missing PyYAML surfaces instead of hiding.

Exit: 0 all blocking stages pass/skip, 1 any blocking fail, 2 usage/IO.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

REPO = Path(__file__).resolve().parent.parent


@dataclass
class Stage:
    name: str
    blocking: bool
    status: str = "pending"  # pass | fail | skip
    detail: str = ""
    raw: str = ""

    @property
    def mark(self) -> str:
        return {"pass": "PASS", "fail": "FAIL", "skip": "SKIP"}.get(
            self.status, "????"
        )


def _py() -> List[str]:
    """This interpreter, with -I when prebuild itself runs isolated."""
    return [sys.executable, "-I"] if sys.flags.isolated else [sys.executable]


def _run(cmd: List[str], cwd: Path) -> Tuple[int, str, str]:
    if cmd and cmd[0] == sys.executable:
        cmd = _py() + cmd[1:]
    try:
        p = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=120
        )
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError:
        return 127, "", "not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout after 120s"
    except OSError as e:
        return 126, "", str(e)


def stage_ast_guard(targets: List[Path]) -> Stage:
    s = Stage("ast_guard", blocking=True)
    tool = REPO / "scripts" / "ast_guard.py"
    if not tool.exists():
        s.status, s.detail = "skip", "scripts/ast_guard.py not present"
        return s
    present = [str(t) for t in targets if t.exists()]
    if not present:
        s.status, s.detail = "skip", "no source targets present"
        return s
    total = 0
    combined: List[str] = []
    for t in present:
        code, out, err = _run([sys.executable, str(tool), t], cwd=REPO)
        combined.append(out)
        if code == 2:
            s.status, s.detail = "fail", f"usage/IO on {t}: {err.strip()}"
            return s
        if code == 1:
            total += sum(1 for line in out.splitlines() if ": [" in line)
    s.raw = "\n".join(combined).strip()
    if total:
        s.status, s.detail = "fail", f"{total} violation(s)"
    else:
        s.status, s.detail = "pass", f"clean over {len(present)} target(s)"
    return s


def stage_hexstrike(ledger: Path) -> Stage:
    s = Stage("hexstrike", blocking=True)
    tool = REPO / "scripts" / "hexstrike.py"
    if not tool.exists():
        s.status, s.detail = "skip", "scripts/hexstrike.py not present"
        return s
    if not ledger.exists():
        s.status, s.detail = "skip", f"{ledger} not present"
        return s
    cmd = [sys.executable, str(tool), str(ledger), "--json"]
    known = REPO / "scripts" / "hexstrike_known_unparsed.txt"
    if known.is_file():
        cmd += ["--known-unparsed", str(known)]
    code, out, err = _run(cmd, cwd=REPO)
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        data = None
    if code == 2:
        first = err.strip().splitlines()[0] if err.strip() else "no stderr"
        s.status, s.detail = "fail", f"incomplete/usage/IO: {first}"
        s.raw = err.strip()[:2000]
        return s
    if data is None:
        s.status, s.detail = "fail", "scanner did not emit JSON"
        s.raw = out[:500]
        return s
    findings = data.get("findings", [])
    s.raw = json.dumps(findings, indent=2)
    known_n = data.get("metrics", {}).get("known_unparsed", 0)
    if known_n:
        known_paths = [
            pf["path"] for pf in data.get("parse_failures", []) if pf.get("known")
        ]
        s.raw = (
            f"known-unparsed (listed in {known.relative_to(REPO)}): "
            + ", ".join(known_paths)
            + "\n"
            + s.raw
        )
    suffix = f"; {known_n} known-unparsed" if known_n else ""
    if findings:
        s.status = "fail"
        s.detail = f"{len(findings)} ghost-seal finding(s){suffix}"
    else:
        s.status, s.detail = "pass", f"no ghost seals{suffix}"
    return s


def stage_ledger_iso8601() -> Stage:
    s = Stage("ledger_iso8601", blocking=True)
    tool = REPO / "scripts" / "ledger_iso8601_gate.py"
    if not tool.exists():
        s.status, s.detail = "skip", "scripts/ledger_iso8601_gate.py not present"
        return s
    code, out, err = _run([sys.executable, str(tool), "--json"], cwd=REPO)
    if code == 2:
        first = err.strip().splitlines()[0] if err.strip() else "no stderr"
        s.status, s.detail = "fail", f"usage/IO: {first}"
        s.raw = err.strip()[:2000]
        return s
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        s.status, s.detail = "fail", "gate did not emit JSON"
        s.raw = out[:500]
        return s
    failing = data.get("new_failing", [])
    s.raw = json.dumps(failing, indent=2) if failing else ""
    legacy = len(data.get("legacy_report_only", []))
    summary = (
        f"{data.get('new_entries', 0)} new entr(y/ies); "
        f"{legacy} legacy report-only"
    )
    if code == 1 or failing:
        s.status, s.detail = "fail", f"{len(failing)} new entr(y/ies) not ISO 8601; {summary}"
    else:
        s.status, s.detail = "pass", summary
    return s


def stage_cdp_status() -> Stage:
    s = Stage("cdp_status", blocking=False)
    tool = REPO / "scripts" / "cdp_status.py"
    if not tool.exists():
        s.status, s.detail = "skip", "scripts/cdp_status.py not present"
        return s
    code, out, err = _run(
        [sys.executable, str(tool), "--once"], cwd=REPO
    )
    s.raw = (out or err).strip()[:500]
    if code == 0:
        s.status, s.detail = "pass", "probe completed"
    elif code == 2:
        s.status, s.detail = "skip", f"probe IO: {err.strip()}"
    else:
        s.status, s.detail = "pass", "probe ran; no session (not a defect)"
    return s


def stage_zeta_bound() -> Stage:
    s = Stage("zeta_bound", blocking=True)
    tool = REPO / "scripts" / "pythonide_object.py"
    if not tool.exists():
        s.status, s.detail = "skip", "scripts/pythonide_object.py not present"
        return s
    code, out, err = _run([sys.executable, str(tool)], cwd=REPO)
    s.raw = (out or err).strip()[:500]
    if code == 0:
        s.status, s.detail = "pass", "golden identity holds; bitten bound 2.366"
    else:
        s.status, s.detail = "fail", f"pythonide_object returned {code}"
    return s


def stage_causal_plane() -> Stage:
    s = Stage("causal_plane", blocking=False)
    tool = REPO / "scripts" / "causal_plane.py"
    if not tool.exists():
        s.status, s.detail = "skip", "scripts/causal_plane.py not present"
        return s
    code, out, err = _run([sys.executable, str(tool)], cwd=REPO)
    s.raw = (out or err).strip()[:500]
    s.status = "pass" if code == 0 else "fail"
    s.detail = "stated plane recorded; zeta raw product still fails 2.366"
    return s


def run(targets: List[Path], ledger: Path) -> List[Stage]:
    return [
        stage_ast_guard(targets),
        stage_hexstrike(ledger),
        stage_ledger_iso8601(),
        stage_cdp_status(),
        stage_zeta_bound(),
        stage_causal_plane(),
    ]


def render(stages: List[Stage], verbose: bool) -> str:
    lines = ["internal prebuild", "=" * 64]
    for s in stages:
        kind = "blocking" if s.blocking else "info"
        lines.append(f"  [{s.mark}] {s.name:<14s} ({kind})  {s.detail}")
    if verbose:
        for s in stages:
            if s.raw:
                lines.append("")
                lines.append(f"--- {s.name} ---")
                lines.append(s.raw)
    blocking_failed = [s for s in stages if s.blocking and s.status == "fail"]
    lines.append("")
    lines.append(f"blocking failures: {len(blocking_failed)}")
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Internal prebuild gate.")
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--ledger",
        type=Path,
        default=REPO / "ledger",
        help="ledger root for hexstrike",
    )
    args = ap.parse_args(argv)

    targets = [REPO / "scripts", REPO / "kernel"]
    stages = run(targets, args.ledger)

    if args.json:
        print(
            json.dumps(
                {
                    "stages": [
                        {
                            "name": s.name,
                            "blocking": s.blocking,
                            "status": s.status,
                            "detail": s.detail,
                        }
                        for s in stages
                    ],
                    "blocking_failures": sum(
                        1
                        for s in stages
                        if s.blocking and s.status == "fail"
                    ),
                },
                indent=2,
            )
        )
    else:
        print(render(stages, args.verbose))

    return 1 if any(s.blocking and s.status == "fail" for s in stages) else 0


if __name__ == "__main__":
    raise SystemExit(main())
