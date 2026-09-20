#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/verify_tree.py — directed tree integrity.

Checks:
  1. Non-empty node set
  2. Exactly one root (parent is null/None/absent)
  3. Every non-root parent id exists in the node set
  4. No cycles (DFS color: white/gray/black)

Input formats (auto-detected by suffix, or --format):
  .json  {"nodes": {"id": {"parent": null|"id", ...}, ...}}
  .yaml  same shape under key `nodes` (requires PyYAML)

Exit codes:
  0  tree is valid
  1  one or more structural violations
  2  file missing, unparseable, or usage error

This script does not write ledger entries. It does not bind ports.
Optional pythonIDE fallback for timed node attributes is out of scope
here; see pythonIDE/symplectic_euler.py for reversible time steps.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def normalize_parent(p: Any) -> Optional[str]:
    if p is None:
        return None
    if isinstance(p, str) and p.strip().lower() in ("", "null", "none"):
        return None
    return str(p)


def extract_nodes(doc: Any) -> Dict[str, Dict[str, Any]]:
    """Accept {nodes: {...}} or a bare mapping of id -> node."""
    if not isinstance(doc, dict):
        raise ValueError("document must be a mapping")
    if "nodes" in doc:
        raw = doc["nodes"]
    else:
        raw = doc
    if not isinstance(raw, dict):
        raise ValueError("'nodes' must be a mapping of id -> node")
    out: Dict[str, Dict[str, Any]] = {}
    for nid, node in raw.items():
        if node is None:
            node = {}
        if not isinstance(node, dict):
            raise ValueError(f"node {nid!r} must be a mapping")
        n = dict(node)
        n["parent"] = normalize_parent(n.get("parent"))
        out[str(nid)] = n
    return out


def verify_tree(nodes: Dict[str, Dict[str, Any]]) -> List[str]:
    """Return a list of problem strings; empty means OK."""
    problems: List[str] = []
    if not nodes:
        return ["empty tree"]

    ids = set(nodes)
    roots: List[str] = []

    for nid, n in nodes.items():
        parent = n.get("parent")
        if parent is None:
            roots.append(nid)
        elif parent not in ids:
            problems.append(f"{nid}: parent {parent!r} does not exist")

    if len(roots) != 1:
        problems.append(f"root count={len(roots)} expected 1: {roots}")

    # Cycle detection: walk toward root; gray = in current path.
    color = {i: 0 for i in ids}  # 0 white, 1 gray, 2 black

    def dfs(u: str) -> None:
        color[u] = 1
        p = nodes[u].get("parent")
        if p is not None and p in color:
            if color[p] == 1:
                problems.append(f"cycle involving {u} -> {p}")
            elif color[p] == 0:
                dfs(p)
        color[u] = 2

    for i in ids:
        if color[i] == 0:
            dfs(i)

    return problems


def load_document(path: Path, fmt: Optional[str] = None) -> Any:
    text = path.read_text(encoding="utf-8")
    kind = (fmt or path.suffix.lstrip(".")).lower()
    if kind in ("yml", "yaml"):
        if not HAS_YAML:
            raise RuntimeError("PyYAML required for YAML input")
        return yaml.safe_load(text)
    if kind == "json":
        return json.loads(text)
    # try JSON then YAML
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        if HAS_YAML:
            return yaml.safe_load(text)
        raise


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Verify directed tree integrity.")
    ap.add_argument(
        "path",
        nargs="?",
        default=None,
        help="JSON/YAML tree file (omit for embedded smoke)",
    )
    ap.add_argument(
        "--format",
        choices=("json", "yaml", "yml"),
        default=None,
        help="force format",
    )
    ap.add_argument(
        "--smoke",
        action="store_true",
        help="run built-in positive/negative cases and exit",
    )
    args = ap.parse_args(argv)

    if args.smoke or args.path is None:
        # Positive
        ok = verify_tree(
            {"a": {"parent": None}, "b": {"parent": "a"}, "c": {"parent": "b"}}
        )
        if ok:
            print("FAIL smoke positive:", ok)
            return 1
        # Missing parent
        bad = verify_tree({"a": {"parent": "z"}})
        if not any("does not exist" in p for p in bad):
            print("FAIL smoke missing-parent:", bad)
            return 1
        # Cycle
        cyc = verify_tree({"a": {"parent": "b"}, "b": {"parent": "a"}})
        if not any("cycle" in p for p in cyc):
            print("FAIL smoke cycle:", cyc)
            return 1
        # Two roots
        two = verify_tree({"a": {"parent": None}, "b": {"parent": None}})
        if not any("root count" in p for p in two):
            print("FAIL smoke two-roots:", two)
            return 1
        print("OK: verify_tree smoke (positive + 3 negatives)")
        if args.path is None and not args.smoke:
            return 0
        if args.smoke and args.path is None:
            return 0

    path = Path(args.path)
    if not path.is_file():
        print(f"::error::{path} not found", file=sys.stderr)
        return 2

    try:
        doc = load_document(path, args.format)
        nodes = extract_nodes(doc)
    except Exception as e:
        print(f"::error::parse failed: {e}", file=sys.stderr)
        return 2

    problems = verify_tree(nodes)
    if problems:
        for p in problems:
            print(f"FAIL: {p}")
        return 1

    print(f"OK: tree valid ({len(nodes)} nodes, 1 root)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
