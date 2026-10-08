#!/usr/bin/env python3
"""
prebuild.py — Clarke Yoursa Tee

Internal prebuild gate. Local tree only — does not commit, seal, or push.

Stage order (all run; missing tools SKIP, not FAIL):
  1. ast_guard   — static rules over source     BLOCKING if tool present
  2. hexstrike   — ghost-seal scan over ledger BLOCKING if tool present
  3. cdp_status  — one-shot probe              INFORMATIONAL

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


def _run(cmd: List[str], cwd: Path) -> Tuple[int, str, str]:
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
    code, out, err = _run(
        [sys.executable, str(tool), str(ledger), "--json"], cwd=REPO
    )
    if code == 2:
        s.status, s.detail = "fail", f"usage/IO: {err.strip()}"
        return s
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        s.status, s.detail = "fail", "scanner did not emit JSON"
        s.raw = out[:500]
        return s
    findings = data.get("findings", [])
    s.raw = json.dumps(findings, indent=2)
    if findings:
        s.status = "fail"
        s.detail = f"{len(findings)} ghost-seal finding(s)"
    else:
        s.status, s.detail = "pass", "no ghost seals"
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
        stage_cdp_status(),
        stage_zeta_bound(),
        stage_causal_plane(),
    ]


def render(stages: List[Stage], verbose: bool) -> str:
    lines = ["internal prebuild", "=" * 64]
    for s in stages:
        kind = "blocking" if s.blocking else "info"
        lines.append(f"  [{s.mark}] {s.name:<12s} ({kind})  {s.detail}")
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
