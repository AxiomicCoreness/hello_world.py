#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 🜁∀∞φ² · AST_GUARD · WOOD_DRAGON_0.91 · SEALED
"""
AST_guard.py

A static‑analysis guard that parses Python source into an AST, enforces
structural / semantic rules, and can inject or verify a computed seal
header (`🜁∀∞φ² · … · SEALED · <digest>`) at the top of each file.

Design goals:
  - No imports executed: only `ast.parse` (pure, safe).
  - Rules are declarative and easy to extend.
  - Deterministic, CI‑friendly output (machine + human readable).
  - No file mutation unless `--inject-seal` is explicitly passed.
  - Seal uses the same SHA3‑256 canonical JSON contract as the ledger.

Usage:
  python AST_guard.py path/to/file.py [more.py ...]
  python AST_guard.py --config guard.yaml path/
  python AST_guard.py --json path/
  python AST_guard.py --inject-seal path/to/file.py
  python AST_guard.py --verify-seal path/

Exit codes:
  0 = all files pass
  1 = at least one violation or seal mismatch
  2 = usage / IO / config error
"""

from __future__ import annotations

# ═════════════════════════════════════════════════════════════════════════════
# SECTION 0 — IMPORTS
# ═════════════════════════════════════════════════════════════════════════════
import argparse
import ast
import hashlib
import json
import math
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable, Iterable, List, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 1 — GOLDEN CONSTANTS (used to seed the seal domain)
# ═════════════════════════════════════════════════════════════════════════════
phi = (1 + math.sqrt(5)) / 2                # 1.618033988749895
phi2 = phi ** 2                              # 2.618033988749895
phi3 = phi ** 3
phi4 = phi ** 4
phi5 = phi ** 5
phi6 = phi ** 6
phi7 = phi ** 7
phi8 = phi ** 8
phi9 = phi ** 9
phi12 = phi ** 12
phi13 = phi ** 13
phi14 = phi ** 14
phi34 = phi ** 34
phi709 = phi ** 709
phi713 = phi ** 713
phi_minus_709 = phi ** (-709)
phi_minus_1000 = phi ** (-1000)
phi_inv = 1 / phi

chi = math.exp(-phi)
t_phi = 0.5983
f0 = 6.49
CUTOFF = 7.5
UNIVERSAL_144 = phi ** 12

PENTAGONAL_ANCHOR = 1 / math.sqrt(5)
REFINED_TS = 1625.622131
SIGNATURE = "8F1A3D9C04B27E5E6A8F2DC47B59E330"
DIM_577 = 577
BOSTON_HEARTBEAT = 42.36

# Seal domain separator — same style as GARDEN.EVENT.v1, GARDEN.LEARNER.v1
SEAL_DOMAIN = "GARDEN.ASTGUARD.v1"


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 2 — RULE MODEL
# ═════════════════════════════════════════════════════════════════════════════
@dataclass
class Violation:
    code: str
    message: str
    file: str
    line: int
    col: int
    node_type: str

    def fmt(self) -> str:
        return f"{self.file}:{self.line}:{self.col}: [{self.code}] {self.message} ({self.node_type})"


@dataclass
class RuleContext:
    filename: str
    source: str
    tree: ast.AST
    parents: dict
    violations: List[Violation] = field(default_factory=list)

    def report(self, code: str, msg: str, node: ast.AST) -> None:
        self.violations.append(Violation(
            code=code,
            message=msg,
            file=self.filename,
            line=getattr(node, "lineno", 0),
            col=getattr(node, "col_offset", 0),
            node_type=type(node).__name__,
        ))


Rule = Callable[[ast.AST, RuleContext], None]


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 3 — DEFAULT RULES (A1–A5, C1, C2)
# ═════════════════════════════════════════════════════════════════════════════
def rule_A1_no_eval_exec(tree: ast.AST, ctx: RuleContext) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in {"eval", "exec"}:
                ctx.report("A1", f"forbidden call to `{node.func.id}`", node)


def rule_A2_no_dunder_import(tree: ast.AST, ctx: RuleContext) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("__") and alias.name.endswith("__"):
                    ctx.report("A2", f"forbidden dunder import `{alias.name}`", node)
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("__") and node.module.endswith("__"):
                ctx.report("A2", f"forbidden dunder import-from `{node.module}`", node)


def rule_A3_no_silent_except(tree: ast.AST, ctx: RuleContext) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            ctx.report("A3", "bare `except:` is forbidden; name the exception", node)


def rule_A4_no_mutable_defaults(tree: ast.AST, ctx: RuleContext) -> None:
    mutable = (ast.List, ast.Dict, ast.Set)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for default in list(node.args.defaults) + list(node.args.kw_defaults):
                if isinstance(default, mutable):
                    ctx.report("A4", "mutable default argument", default)


def rule_A5_no_top_level_side_effects(tree: ast.AST, ctx: RuleContext) -> None:
    if not isinstance(tree, ast.Module):
        return

    def is_dunder_main(node: ast.If) -> bool:
        t = node.test
        return (
            isinstance(t, ast.Compare)
            and isinstance(t.left, ast.Name)
            and t.left.id == "__name__"
            and len(t.comparators) == 1
            and isinstance(t.comparators[0], ast.Constant)
            and t.comparators[0].value == "__main__"
        )

    for node in tree.body:
        ok = (
            isinstance(node, (ast.Import, ast.ImportFrom,
                              ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.ClassDef, ast.AnnAssign, ast.Assign))
            or (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str))
            or (isinstance(node, ast.If) and is_dunder_main(node))
            or isinstance(node, ast.Try)
        )
        if not ok:
            ctx.report("A5", f"top-level `{type(node).__name__}` not allowed (side effect risk)", node)


def rule_C1_no_sealed_rewrite(tree: ast.AST, ctx: RuleContext) -> None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for t in targets:
                if isinstance(t, ast.Name) and t.id.startswith("SEALED_"):
                    ctx.report("C1", f"sealed name `{t.id}` must not be rewritten", t)


def rule_C2_no_ledger_mutation(tree: ast.AST, ctx: RuleContext) -> None:
    banned_methods = {"rewrite_ledger", "mutate_ledger", "seal_overwrite"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Attribute) and f.attr in banned_methods:
                ctx.report("C2", f"ledger mutation `{f.attr}` is forbidden", node)
            if isinstance(f, ast.Name) and f.id in banned_methods:
                ctx.report("C2", f"ledger mutation `{f.id}` is forbidden", node)


DEFAULT_RULES: List[Rule] = [
    rule_A1_no_eval_exec,
    rule_A2_no_dunder_import,
    rule_A3_no_silent_except,
    rule_A4_no_mutable_defaults,
    rule_A5_no_top_level_side_effects,
    rule_C1_no_sealed_rewrite,
    rule_C2_no_ledger_mutation,
]


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 4 — COMPUTED SEAL HEADER (injection & verification)
# ═════════════════════════════════════════════════════════════════════════════
SEAL_LINE_RE = re.compile(
    r"^#\s*🜁∀∞φ²\s*·[^\n]*·\s*SEALED\s*·\s*([0-9a-f]{64})\s*$",
    re.MULTILINE,
)


def compute_seal(source: str, *, domain: str = SEAL_DOMAIN) -> str:
    """
    Compute the SHA3‑256 seal over the canonical JSON of the file's
    source content, prefixed with a domain separator.

    Normalisation:
      - line endings → LF
      - no trailing whitespace on lines
      - exactly one trailing newline
    """
    normalised = "\n".join(line.rstrip() for line in source.replace("\r\n", "\n").split("\n"))
    if not normalised.endswith("\n"):
        normalised += "\n"

    payload = {"domain": domain, "content": normalised}
    canon = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha3_256(canon.encode("utf-8")).hexdigest()


def build_seal_line(digest: str, *, tag: str = "AST_GUARD") -> str:
    return f"# 🜁∀∞φ² · {tag} · WOOD_DRAGON_0.91 · SEALED · {digest}"


def has_seal_header(source: str) -> Optional[str]:
    m = SEAL_LINE_RE.search(source)
    return m.group(1) if m else None


def _split_header(source: str) -> tuple[str, str, str]:
    """Return (shebang, encoding_line, body) with any seal line removed."""
    stripped = SEAL_LINE_RE.sub("", source, count=1)
    lines = stripped.split("\n")
    shebang = ""
    if lines and lines[0].startswith("#!"):
        shebang = lines[0] + "\n"
        lines = lines[1:]
    encoding_line = ""
    if lines and re.match(r"^#.*coding[:=]", lines[0]):
        encoding_line = lines[0] + "\n"
        lines = lines[1:]
    body = "\n".join(lines)
    return shebang, encoding_line, body


def inject_seal(path: Path, *, tag: str = "AST_GUARD") -> tuple[bool, str, str]:
    source = path.read_text(encoding="utf-8")
    old_digest = has_seal_header(source) or ""
    shebang, encoding_line, body = _split_header(source)

    new_digest = compute_seal(shebang + encoding_line + body, domain=SEAL_DOMAIN)
    seal_line = build_seal_line(new_digest, tag=tag) + "\n"

    new_source = shebang + encoding_line + seal_line + body
    if new_source == source:
        return (False, old_digest, new_digest)

    path.write_text(new_source, encoding="utf-8")
    return (True, old_digest, new_digest)


def verify_seal(path: Path) -> tuple[bool, str, str]:
    source = path.read_text(encoding="utf-8")
    found = has_seal_header(source) or ""
    shebang, encoding_line, body = _split_header(source)
    expected = compute_seal(shebang + encoding_line + body, domain=SEAL_DOMAIN)
    return (found == expected, expected, found)


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 5 — CONFIG LOADING (YAML)
# ═════════════════════════════════════════════════════════════════════════════
def load_config(path: Path) -> dict:
    if not HAS_YAML:
        raise RuntimeError("PyYAML is required for --config; install pyyaml")
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def build_rules_from_config(cfg: dict) -> List[Rule]:
    if not cfg or "rules" not in cfg:
        return DEFAULT_RULES
    wanted = set(cfg["rules"])
    mapping = {
        "A1": rule_A1_no_eval_exec,
        "A2": rule_A2_no_dunder_import,
        "A3": rule_A3_no_silent_except,
        "A4": rule_A4_no_mutable_defaults,
        "A5": rule_A5_no_top_level_side_effects,
        "C1": rule_C1_no_sealed_rewrite,
        "C2": rule_C2_no_ledger_mutation,
    }
    return [mapping[k] for k in wanted if k in mapping]


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 6 — RUNNER
# ═════════════════════════════════════════════════════════════════════════════
def build_parent_map(tree: ast.AST) -> dict:
    parents: dict = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[id(child)] = parent
    return parents


def check_file(path: Path, rules: Iterable[Rule]) -> List[Violation]:
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return [Violation("IO", f"cannot read file: {e}", str(path), 0, 0, "File")]

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as e:
        return [Violation("SYNTAX", f"syntax error: {e.msg}", str(path),
                          e.lineno or 0, e.offset or 0, "SyntaxError")]

    ctx = RuleContext(
        filename=str(path),
        source=source,
        tree=tree,
        parents=build_parent_map(tree),
    )
    for rule in rules:
        rule(tree, ctx)
    return ctx.violations


def iter_python_files(targets: List[str]) -> Iterable[Path]:
    for t in targets:
        p = Path(t)
        if p.is_dir():
            for f in sorted(p.rglob("*.py")):
                if any(part in {".git", "__pycache__", ".venv", "venv", "build", "dist"}
                       for part in f.parts):
                    continue
                yield f
        elif p.is_file():
            yield p
        else:
            print(f"warning: not found: {p}", file=sys.stderr)


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 7 — MAIN
# ═════════════════════════════════════════════════════════════════════════════
def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description="AST_guard: static AST rule enforcement + computed seal header."
    )
    ap.add_argument("targets", nargs="+", help="files or directories to check")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--quiet", action="store_true", help="only print violations, no summary")
    ap.add_argument("--config", type=str, default=None, help="path to YAML config")
    ap.add_argument("--inject-seal", action="store_true",
                    help="inject/refresh the computed seal header on each file")
    ap.add_argument("--verify-seal", action="store_true",
                    help="verify the computed seal header on each file")
    args = ap.parse_args(argv)

    # Load rules
    rules = DEFAULT_RULES
    if args.config:
        try:
            cfg = load_config(Path(args.config))
            rules = build_rules_from_config(cfg)
        except Exception as e:
            print(f"config error: {e}", file=sys.stderr)
            return 2

    all_violations: List[Violation] = []
    files_checked = 0
    seal_report: List[dict] = []

    for path in iter_python_files(args.targets):
        files_checked += 1

        if args.inject_seal:
            try:
                changed, old_d, new_d = inject_seal(path)
                seal_report.append({
                    "file": str(path), "action": "inject_seal",
                    "changed": changed, "old_digest": old_d, "new_digest": new_d,
                })
            except OSError as e:
                all_violations.append(Violation("IO", f"seal inject failed: {e}",
                                                str(path), 0, 0, "File"))

        if args.verify_seal:
            try:
                ok, exp, found = verify_seal(path)
                seal_report.append({
                    "file": str(path), "action": "verify_seal",
                    "ok": ok, "expected": exp, "found": found,
                })
            except OSError as e:
                all_violations.append(Violation("IO", f"seal verify failed: {e}",
                                                str(path), 0, 0, "File"))

        # Run AST rules only when we did not exclusively ask for seal ops.
        if not (args.inject_seal or args.verify_seal):
            all_violations.extend(check_file(path, rules))

    # Output
    if args.json:
        print(json.dumps({
            "files_checked": files_checked,
            "violations": [asdict(v) for v in all_violations],
            "seal_report": seal_report,
        }, indent=2))
    else:
        for v in all_violations:
            print(v.fmt())
        for r in seal_report:
            if r["action"] == "inject_seal":
                mark = "🖋" if r["changed"] else "✓"
                print(f"{mark} {r['file']}  new={r['new_digest'][:16]}…  old={r['old_digest'][:16] or '—'}")
            else:
                mark = "✅" if r["ok"] else "❌"
                print(f"{mark} {r['file']}  expected={r['expected'][:16]}…  found={r['found'][:16] or '—'}")
        if not args.quiet:
            print(f"\n[{files_checked} file(s) checked, "
                  f"{len(all_violations)} violation(s), "
                  f"{len(seal_report)} seal operation(s)]", file=sys.stderr)

    # Exit code
    if all_violations:
        return 1
    if args.verify_seal and any(not r.get("ok", True) for r in seal_report):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
