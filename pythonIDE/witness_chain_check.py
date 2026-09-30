#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
witness_chain_check.py — emit | list | assert-count | distribution

Node runs report PRESENT_ON_NODE (exit 5).
Source-of-record (main) reports WIRED (exit 0) when imports succeed.
Does not claim seal-preimage knowledge (Contract A).
assert-count measures the run tree only (Contract B).

CI note: GitHub Actions checkouts are detached HEADs, so
git rev-parse --abbrev-ref HEAD returns "HEAD" and can never report the
branch. current_branch() therefore prefers the GitHub event context
(GITHUB_HEAD_REF for pull_request events, GITHUB_REF_NAME for push events)
before falling back to git. Without this, a run on main misclassifies as
a node run (exit 5) and renders red in CI.

Exit codes:
  0  verified on source-of-record
  1  assert-count import failures
  2  triple import failed
  5  verified on node only (tree-distribution pending)
  6  distribution probe failed
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


def current_branch() -> str:
    # CI-aware: prefer the GitHub event context when present.
    env = os.environ.get("GITHUB_HEAD_REF") or os.environ.get("GITHUB_REF_NAME")
    if env and env.strip():
        return env.strip()
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return out.stdout.strip() or "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def current_head() -> str:
    env = os.environ.get("GITHUB_SHA")
    if env and env.strip():
        return env.strip()
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return out.stdout.strip() or "UNKNOWN"
    except Exception:
        return "UNKNOWN"


def _load_triple():
    try:
        return importlib.import_module("pythonIDE.witness_chain_triple")
    except Exception:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        try:
            return importlib.import_module("pythonIDE.witness_chain_triple")
        except Exception as e:
            print(
                json.dumps(
                    {
                        "status": "FAIL",
                        "reason": "triple_import_failed",
                        "error": str(e),
                    },
                    indent=2,
                )
            )
            sys.exit(2)


def emit() -> int:
    triple = _load_triple()
    branch = current_branch()
    head = current_head()
    is_sor = branch == triple.SOURCE_OF_RECORD
    try:
        matrix = triple.distribution_probe()
        wired = triple.wiredness()
    except Exception as e:
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "reason": "distribution_probe_failed",
                    "error": str(e),
                    "branch": branch,
                    "head": head,
                },
                indent=2,
            )
        )
        return 6

    status = "WIRED" if is_sor else "PRESENT_ON_NODE"
    scope = (
        "verified_on_source_of_record"
        if is_sor
        else "verified_on_node_only_tree_distribution_pending"
    )
    payload: Dict[str, Any] = {
        "status": status,
        "scope": scope,
        "branch": branch,
        "head": head,
        "source_of_record": triple.SOURCE_OF_RECORD,
        "is_source_of_record": is_sor,
        "contract_names": [n for n, _ in triple.CONTRACTS],
        "governed_files": list(triple.GOVERNED_FILES),
        "distribution": matrix,
        "wiredness": wired,
        "claim_language_note": (
            "assert-count measures the run tree only; "
            "wiredness requires presence on the source-of-record tree"
        ),
    }
    print(json.dumps(payload, indent=2, default=str))
    return 0 if is_sor else 5


def list_files() -> int:
    triple = _load_triple()
    for f in triple.GOVERNED_FILES:
        print(f)
    return 0


def distribution() -> int:
    triple = _load_triple()
    try:
        print(json.dumps(triple.distribution_probe(), indent=2))
        return 0
    except Exception as e:
        print(json.dumps({"status": "FAIL", "error": str(e)}, indent=2))
        return 6


def assert_count() -> int:
    triple = _load_triple()
    branch = current_branch()
    head = current_head()
    is_sor = branch == triple.SOURCE_OF_RECORD
    checked: List[Dict[str, Any]] = []
    failures = 0
    for f in triple.GOVERNED_FILES:
        mod_path = f.replace("/", ".").removesuffix(".py")
        entry: Dict[str, Any] = {"file": f, "module": mod_path}
        try:
            importlib.import_module(mod_path)
            entry["imported"] = True
        except Exception as e:
            entry["imported"] = False
            entry["error"] = str(e)
            failures += 1
        checked.append(entry)
    try:
        matrix = triple.distribution_probe()
        wired = triple.wiredness()
    except Exception:
        matrix, wired = {}, {}
    payload = {
        "branch": branch,
        "head": head,
        "is_source_of_record": is_sor,
        "count": len(checked),
        "failures": failures,
        "checked": checked,
        "distribution": matrix,
        "wiredness": wired,
        "scope": (
            "verified_on_source_of_record"
            if is_sor
            else "verified_on_node_only_tree_distribution_pending"
        ),
        "contract_B_note": (
            "assert-count measures the run tree; wiredness requires "
            "presence on source-of-record"
        ),
    }
    print(json.dumps(payload, indent=2, default=str))
    if failures:
        return 1
    return 0 if is_sor else 5


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(prog="witness_chain_check.py")
    ap.add_argument(
        "cmd", choices=["emit", "list", "assert-count", "distribution"]
    )
    args = ap.parse_args(argv)
    return {
        "emit": emit,
        "list": list_files,
        "assert-count": assert_count,
        "distribution": distribution,
    }[args.cmd]()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
