#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 🜁∀∞φ² · AST_GUARD_D1 · WOOD_DRAGON_0.91 · SEALED
"""
AST_guard_rule_d1.py — standalone D1 gate.

Standalone gate:
    python3 AST_guard_rule_d1.py FILE [FILE ...]

Exit 0 = clean; exit 1 = stale imports found.
Grep is discovery; this gate is enforcement. Once wired into CI, the
discovery grep is redundant.

D29 provenance: pre-integration gate SHA was
    e504dd1ead4cc60021c564615e6ca1e544b5972e
Retained as documentation only.
"""

from __future__ import annotations

import ast
import sys
from typing import Iterable, Iterator, Sequence, Tuple

D1_PROVENANCE_SHA: str = "e504dd1ead4cc60021c564615e6ca1e544b5972e"

STALE_IMPORT_PREFIXES: Tuple[str, ...] = (
    "celestial.strike_ix",
    "celestial.saturn_soul_cannon_strike_ix",
    "prometheus.trappist_metrics_draft",
)


def is_stale_module(module_name: str) -> bool:
    return any(
        module_name == p or module_name.startswith(p + ".")
        for p in STALE_IMPORT_PREFIXES
    )


class D1Context:
    def __init__(self) -> None:
        self.failures: list[Tuple[str, str, int]] = []

    def report(self, rule_id: str, message: str, node: ast.AST) -> None:
        self.failures.append(
            (rule_id, message, getattr(node, "lineno", 0))
        )


def rule_D1_no_stale_module_paths(tree: ast.AST, ctx: D1Context) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if is_stale_module(alias.name):
                    ctx.report(
                        "D1",
                        "stale module path '%s' (use the flattened form)"
                        % alias.name,
                        node,
                    )
        elif isinstance(node, ast.ImportFrom):
            if node.module and is_stale_module(node.module):
                ctx.report(
                    "D1",
                    "stale module path '%s' (use the flattened form)"
                    % node.module,
                    node,
                )


def scan_paths(paths: Sequence[str]) -> int:
    total = 0
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                tree = ast.parse(handle.read(), filename=path)
        except (OSError, UnicodeDecodeError, SyntaxError) as e:
            print("%s: SKIP: %s" % (path, e), file=sys.stderr)
            continue
        ctx = D1Context()
        rule_D1_no_stale_module_paths(tree, ctx)
        for rule_id, message, lineno in ctx.failures:
            print("%s:%d: %s: %s" % (path, lineno, rule_id, message))
            total += 1
    if total:
        return 1
    print("D1: no stale module paths")
    return 0


def _cli(argv: Sequence[str]) -> int:
    if not argv:
        print("usage: AST_guard_rule_d1.py FILE [FILE ...]", file=sys.stderr)
        return 2
    return scan_paths(argv)


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv[1:]))
