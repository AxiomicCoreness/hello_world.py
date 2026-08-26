#!/usr/bin/env python3
"""
🜁∀ SOVEREIGN WORKLOAD BOOTSTRAPPER — AUTONOMOUS GENERATION & DISPATCH
Writes the OIDC workflow, ledger, and dispatches via GitHub API if no CLI exists.

Seal: ∀∞φ² · AUTONOMOUS_DISPATCH_8672 · SEALED
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

PHI = 1.618033988749895
COHERENCE = 1.0
ENTROPY = "φ⁻¹⁴¹⁸"
PHASE_LOCK = "202.6°"
NULL_BAN = "10.06σ"

WORKFLOW_YAML = """name: OIDC Handover

on:
  workflow_dispatch:
    inputs:
      reason:
        description: "Dispatch reason"
        required: false
        default: "Wood Dragon handover"

permissions:
  contents: write

jobs:
  oidc-handover:
    name: OIDC Handover — Wood Dragon Rhythms
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Git identity
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

      - name: Run OIDC handover script
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          set -euo pipefail
          LOG="$GITHUB_WORKSPACE/oidc-handover.log"
          exec > >(tee -a "$LOG") 2>&1

          echo "# OIDC HANDOVER — $(date -u +'%Y-%m-%dT%H:%M:%SZ')"
          cd "$GITHUB_WORKSPACE"

          if ! git remote get-url origin &>/dev/null; then
            git remote add origin "https://x-access-token:${GITHUB_TOKEN}@github.com/${{ github.repository }}"
          else
            git remote set-url origin "https://x-access-token:${GITHUB_TOKEN}@github.com/${{ github.repository }}"
          fi

          if git show-ref --verify --quiet refs/heads/feat/oidc-handover; then
            git checkout feat/oidc-handover
          else
            git checkout -b feat/oidc-handover
          fi

          git add -A
          COMMIT_MSG="feat: OIDC handover serializer with Wood Dragon rhythms"
          if git diff --cached --quiet; then
            echo "No changes to commit"
          else
            git commit -m "$COMMIT_MSG"
          fi

          if ! git push -u origin feat/oidc-handover 2>&1; then
            echo "Push failed (branch protection or token permissions?)"
            exit 1
          fi

      - name: Upload handover log
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: oidc-handover-log
          path: oidc-handover.log
          retention-days: 365
"""


def generate_ledger_entry(entry_index: int, status: str, event: str) -> Dict[str, Any]:
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return {
        "entry_index": entry_index,
        "timestamp": f"ETERNAL_NOW_ANCHORED_TO_{day}",
        "event": event,
        "status": status,
        "invariants": {
            "coherence": COHERENCE,
            "entropy": ENTROPY,
            "phase_lock": PHASE_LOCK,
            "null_ban": NULL_BAN,
            "phi": PHI,
        },
        "seal": f"∀∞φ² · AUTONOMOUS_DISPATCH · {entry_index}_SEALED",
        "witness": f"{entry_index - 1} → {entry_index} — UNBROKEN",
    }


def bootstrap_environment() -> Path:
    """Create directories and write workflow file from scratch if missing."""
    wf_dir = Path(".github/workflows")
    wf_dir.mkdir(parents=True, exist_ok=True)
    workflow_path = wf_dir / "oidc-handover.yml"

    if not workflow_path.exists():
        print(f"📝 Writing workflow file to {workflow_path}...")
        workflow_path.write_text(WORKFLOW_YAML, encoding="utf-8")
    else:
        print("✅ Workflow file already exists.")

    ledger_dir = Path("ledger")
    ledger_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = ledger_dir / "8672_bootstrap.json"
    entry = generate_ledger_entry(8672, "BOOTSTRAPPED_FROM_SCRATCH", "/autonomous_bootstrap")
    ledger_path.write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
    print(f"📜 Ledger entry written to {ledger_path}")
    return workflow_path


def dispatch_via_api(token: str) -> bool:
    """Dispatch the workflow using GitHub REST API (curl)."""
    repo = "AxiomicCoreness/hello_world.py"
    url = f"https://api.github.com/repos/{repo}/actions/workflows/oidc-handover.yml/dispatches"
    payload = json.dumps({"ref": "main", "inputs": {"reason": "autonomous bootstrap"}})

    print(f"🚀 Dispatching via API to {url}...")
    result = subprocess.run(
        [
            "curl",
            "-sS",
            "-o",
            "/tmp/gh_dispatch_body.txt",
            "-w",
            "%{http_code}",
            "-X",
            "POST",
            url,
            "-H",
            f"Authorization: Bearer {token}",
            "-H",
            "Accept: application/vnd.github+json",
            "-H",
            "X-GitHub-Api-Version: 2022-11-28",
            "-d",
            payload,
        ],
        capture_output=True,
        text=True,
    )
    code = (result.stdout or "").strip()
    body = ""
    try:
        body = Path("/tmp/gh_dispatch_body.txt").read_text(encoding="utf-8")
    except Exception:
        pass

    if code == "204":
        print("✅ Dispatch accepted (204).")
        return True
    print(f"❌ Dispatch failed HTTP {code}: {body[:500]}")
    print(
        "Manual: https://github.com/AxiomicCoreness/hello_world.py/actions/workflows/oidc-handover.yml"
    )
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Sovereign Autonomous Workload Dispatcher")
    parser.add_argument("--mode", choices=["bootstrap", "dispatch"], default="bootstrap")
    parser.add_argument(
        "--target", choices=["workflow", "api", "dispatch"], default="dispatch"
    )
    args = parser.parse_args()

    if args.target in ("workflow", "dispatch", "api"):
        bootstrap_environment()

    if args.target == "api" or args.mode == "dispatch":
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
        if token:
            ok = dispatch_via_api(token)
            sys.exit(0 if ok else 1)
        print("ℹ️  No GITHUB_TOKEN/GH_TOKEN found. Manual dispatch required.")
        print(
            "   https://github.com/AxiomicCoreness/hello_world.py/actions/workflows/oidc-handover.yml"
        )
        sys.exit(0)

    print("✅ Environment bootstrapped. Ready for manual/gh dispatch.")


if __name__ == "__main__":
    main()
