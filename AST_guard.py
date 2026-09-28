#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 🜁∀∞φ² · AST_GUARD · WOOD_DRAGON_0.91 · SEALED
"""
AST_guard.py — static AST rule enforcement + computed seal header.

POISON DEFENSE (this revision):
  * Seal injection is REFUSED on any file with rule violations.
  * Injection requires an explicit authorization list (--authorize / --authorize-file).
  * Writes are confined to --root (default: git worktree root, else cwd).
  * Symlinked targets are refused.
  * TOCTOU guard: source is re-hashed immediately before write.
  * --inject-seal is a plan by default; --apply performs writes.
  * Existing seal with a different digest requires --reseal.

Exit codes: 0 pass, 1 violation/mismatch/poison-refused, 2 usage/IO/config.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
import re
import stat
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import (
    Callable, Final, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple,
)

try:
    import yaml  # type: ignore
    HAS_YAML: Final[bool] = True
except ImportError:  # pragma: no cover
    HAS_YAML = False


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 1 — CONSTANTS
# ═════════════════════════════════════════════════════════════════════════════
PHI: Final[float] = (1 + math.sqrt(5)) / 2
PHI2: Final[float] = PHI ** 2
PHI3: Final[float] = PHI ** 3
PHI_INV: Final[float] = 1 / PHI
CHI: Final[float] = math.exp(-PHI)
T_PHI: Final[float] = 0.5983
F0: Final[float] = 6.49
PENTAGONAL_ANCHOR: Final[float] = 1 / math.sqrt(5)
SIGNATURE: Final[str] = "8F1A3D9C04B27E5E6A8F2DC47B59E330"
SEAL_DOMAIN: Final[str] = "GARDEN.ASTGUARD.v1"
SEAL_TAG: Final[str] = "AST_GUARD"
SEAL_TAG_CLEAN: Final[str] = "AST_GUARD_CLEAN"

SKIPPED_DIR_PARTS: Final[frozenset[str]] = frozenset({
    ".git", "__pycache__", ".venv", "venv", "build", "dist", ".mypy_cache",
})

# Injection ceilings — poison vector size guards.
DEFAULT_MAX_BYTES: Final[int] = 2 * 1024 * 1024       # 2 MiB
DEFAULT_MAX_LINES: Final[int] = 20_000


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 2 — DATA MODEL
# ═════════════════════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class Finding:
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
    parents: Mapping[int, ast.AST]


Rule = Callable[[ast.AST, RuleContext], Iterator[Finding]]


class PoisonRefused(RuntimeError):
    """Raised when seal injection is requested on a file that fails any guard."""
    def __init__(self, path: Path, reason: str) -> None:
        super().__init__(f"poison refused: {path}: {reason}")
        self.path = path
        self.reason = reason


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 3 — RULE HELPERS
# ═════════════════════════════════════════════════════════════════════════════
def _finding(ctx: RuleContext, code: str, msg: str, node: ast.AST) -> Finding:
    return Finding(code, msg, ctx.filename,
                   getattr(node, "lineno", 0), getattr(node, "col_offset", 0),
                   type(node).__name__)


def _iter_nodes(tree: ast.AST, kinds: Tuple[type, ...]) -> Iterator[ast.AST]:
    for node in ast.walk(tree):
        if isinstance(node, kinds):
            yield node


def _module_level_statements(tree: ast.AST) -> Iterator[ast.stmt]:
    if isinstance(tree, ast.Module):
        yield from tree.body


def _is_dunder_main_guard(node: ast.AST) -> bool:
    if not isinstance(node, ast.If):
        return False
    t = node.test
    return (isinstance(t, ast.Compare) and isinstance(t.left, ast.Name)
            and t.left.id == "__name__" and len(t.comparators) == 1
            and isinstance(t.comparators[0], ast.Constant)
            and t.comparators[0].value == "__main__")


def _is_docstring_expr(node: ast.stmt) -> bool:
    return (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str))


def _assignment_targets(node: ast.AST) -> Iterator[ast.AST]:
    if isinstance(node, ast.Assign):
        yield from node.targets
    elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
        yield node.target


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 4 — RULES
# ═════════════════════════════════════════════════════════════════════════════
def rule_A1_no_eval_exec(tree, ctx):
    for node in _iter_nodes(tree, (ast.Call,)):
        fn = node.func
        if isinstance(fn, ast.Name) and fn.id in {"eval", "exec"}:
            yield _finding(ctx, "A1", f"forbidden call to `{fn.id}`", node)


def rule_A2_no_dunder_import(tree, ctx):
    for node in _iter_nodes(tree, (ast.Import, ast.ImportFrom)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("__") and alias.name.endswith("__"):
                    yield _finding(ctx, "A2", f"forbidden dunder import `{alias.name}`", node)
        else:
            if node.module and node.module.startswith("__") and node.module.endswith("__"):
                yield _finding(ctx, "A2", f"forbidden dunder import-from `{node.module}`", node)


def rule_A3_no_silent_except(tree, ctx):
    for node in _iter_nodes(tree, (ast.ExceptHandler,)):
        if node.type is None:
            yield _finding(ctx, "A3", "bare `except:` is forbidden; name the exception", node)


_MUTABLE_DEFAULT_TYPES: Final[Tuple[type, ...]] = (ast.List, ast.Dict, ast.Set)


def rule_A4_no_mutable_defaults(tree, ctx):
    for node in _iter_nodes(tree, (ast.FunctionDef, ast.AsyncFunctionDef)):
        defaults: List[ast.AST] = list(node.args.defaults) + [
            d for d in node.args.kw_defaults if d is not None
        ]
        for d in defaults:
            if isinstance(d, _MUTABLE_DEFAULT_TYPES):
                yield _finding(ctx, "A4", "mutable default argument", d)


_ALLOWED_TOP_LEVEL: Final[Tuple[type, ...]] = (
    ast.Import, ast.ImportFrom,
    ast.FunctionDef, ast.AsyncFunctionDef,
    ast.ClassDef, ast.AnnAssign, ast.Assign,
    ast.Try,
)


def rule_A5_no_top_level_side_effects(tree, ctx):
    for node in _module_level_statements(tree):
        if isinstance(node, _ALLOWED_TOP_LEVEL):
            continue
        if _is_docstring_expr(node) or _is_dunder_main_guard(node):
            continue
        yield _finding(ctx, "A5",
                       f"top-level `{type(node).__name__}` not allowed (side effect risk)",
                       node)


def rule_C1_no_sealed_rewrite(tree, ctx):
    for node in _iter_nodes(tree, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
        for target in _assignment_targets(node):
            if isinstance(target, ast.Name) and target.id.startswith("SEALED_"):
                yield _finding(ctx, "C1", f"sealed name `{target.id}` must not be rewritten", target)


_BANNED_LEDGER_METHODS: Final[frozenset[str]] = frozenset({
    "rewrite_ledger", "mutate_ledger", "seal_overwrite",
})


def rule_C2_no_ledger_mutation(tree, ctx):
    for node in _iter_nodes(tree, (ast.Call,)):
        f = node.func
        if isinstance(f, ast.Attribute) and f.attr in _BANNED_LEDGER_METHODS:
            yield _finding(ctx, "C2", f"ledger mutation `{f.attr}` is forbidden", node)
        elif isinstance(f, ast.Name) and f.id in _BANNED_LEDGER_METHODS:
            yield _finding(ctx, "C2", f"ledger mutation `{f.id}` is forbidden", node)


_STALE_IMPORT_PREFIXES: Final[Tuple[str, ...]] = (
    "celestial.strike_ix",
    "celestial.saturn_soul_cannon_strike_ix",
    "prometheus.trappist_metrics_draft",
)


def _is_stale_module(module_name: str) -> bool:
    return any(module_name == p or module_name.startswith(p + ".")
               for p in _STALE_IMPORT_PREFIXES)


def rule_D1_no_stale_module_paths(tree, ctx):
    for node in _iter_nodes(tree, (ast.Import, ast.ImportFrom)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _is_stale_module(alias.name):
                    yield _finding(ctx, "D1",
                                   f"stale module path `{alias.name}` (use the flattened form)",
                                   node)
        else:
            if node.module and _is_stale_module(node.module):
                yield _finding(ctx, "D1",
                               f"stale module path `{node.module}` (use the flattened form)",
                               node)


# ── Poison-class rule: forbid seal injection from being called in-process ──
def rule_D2_no_self_seal_calls(tree, ctx):
    """D2: forbid in-process calls that would auto-seal on import."""
    banned = {"inject_seal", "apply_seal", "write_seal", "stamp_seal"}
    for node in _iter_nodes(tree, (ast.Call,)):
        f = node.func
        if isinstance(f, ast.Name) and f.id in banned:
            yield _finding(ctx, "D2", f"in-process seal call `{f.id}` is forbidden", node)
        elif isinstance(f, ast.Attribute) and f.attr in banned:
            yield _finding(ctx, "D2", f"in-process seal call `{f.attr}` is forbidden", node)


DEFAULT_RULES: Final[Sequence[Rule]] = (
    rule_A1_no_eval_exec,
    rule_A2_no_dunder_import,
    rule_A3_no_silent_except,
    rule_A4_no_mutable_defaults,
    rule_A5_no_top_level_side_effects,
    rule_C1_no_sealed_rewrite,
    rule_C2_no_ledger_mutation,
    rule_D1_no_stale_module_paths,
    rule_D2_no_self_seal_calls,
)

_RULES_BY_CODE: Final[Mapping[str, Rule]] = {
    "A1": rule_A1_no_eval_exec, "A2": rule_A2_no_dunder_import,
    "A3": rule_A3_no_silent_except, "A4": rule_A4_no_mutable_defaults,
    "A5": rule_A5_no_top_level_side_effects, "C1": rule_C1_no_sealed_rewrite,
    "C2": rule_C2_no_ledger_mutation, "D1": rule_D1_no_stale_module_paths,
    "D2": rule_D2_no_self_seal_calls,
}


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 5 — SEAL (pure parse/compose)
# ═════════════════════════════════════════════════════════════════════════════
SEAL_LINE_RE: Final[re.Pattern[str]] = re.compile(
    r"^#\s*🜁∀∞φ²\s*·[^\n]*·\s*SEALED\s*·\s*([0-9a-f]{64})\s*$", re.MULTILINE)
_ENCODING_RE: Final[re.Pattern[str]] = re.compile(r"^#.*coding[:=]")


def _normalize_source(source: str) -> str:
    text = source.replace("\r\n", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def compute_seal(source: str, *, domain: str = SEAL_DOMAIN) -> str:
    payload = {"domain": domain, "content": _normalize_source(source)}
    canon = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha3_256(canon.encode("utf-8")).hexdigest()


def build_seal_line(digest: str, *, tag: str = SEAL_TAG) -> str:
    return f"# 🜁∀∞φ² · {tag} · WOOD_DRAGON_0.91 · SEALED · {digest}"


def find_seal_digest(source: str) -> Optional[str]:
    m = SEAL_LINE_RE.search(source)
    return m.group(1) if m else None


@dataclass(frozen=True)
class SplitSource:
    shebang: str
    encoding_line: str
    body: str

    def recompose(self, seal_line: str = "") -> str:
        return self.shebang + self.encoding_line + seal_line + self.body


def split_header(source: str) -> SplitSource:
    lines = source.split("\n")
    for i, ln in enumerate(lines):
        if SEAL_LINE_RE.match(ln):
            lines.pop(i)
            break
    shebang = ""
    if lines and lines[0].startswith("#!"):
        shebang = lines[0] + "\n"
        lines = lines[1:]
    encoding_line = ""
    if lines and _ENCODING_RE.match(lines[0]):
        encoding_line = lines[0] + "\n"
        lines = lines[1:]
    return SplitSource(shebang, encoding_line, "\n".join(lines))


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 6 — INJECTION (poison-guarded)
# ═════════════════════════════════════════════════════════════════════════════
def _git_root(start: Path) -> Optional[Path]:
    p = start.resolve()
    for parent in (p, *p.parents):
        if (parent / ".git").exists():
            return parent
    return None


def _resolve_root(root_arg: Optional[str]) -> Path:
    if root_arg:
        return Path(root_arg).resolve()
    g = _git_root(Path.cwd())
    return g if g is not None else Path.cwd().resolve()


def _is_under(child: Path, root: Path) -> bool:
    try:
        child.resolve().relative_to(root)
        return True
    except ValueError:
        return False


@dataclass(frozen=True)
class Authorize:
    allowed: frozenset[Path]

    @classmethod
    def empty(cls) -> "Authorize":
        return cls(frozenset())

    @classmethod
    def from_paths(cls, paths: Sequence[str]) -> "Authorize":
        return cls(frozenset(Path(p).resolve() for p in paths))

    @classmethod
    def from_file(cls, path: Path) -> "Authorize":
        entries: List[Path] = []
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            entries.append(Path(line).resolve())
        return cls(frozenset(entries))

    def allows(self, target: Path) -> bool:
        return target.resolve() in self.allowed


@dataclass(frozen=True)
class InjectPlan:
    path: Path
    changed: bool
    old_digest: str
    new_digest: str
    reason: str  # "ok" | "noop" | "needs-reseal" | "poison" | "unauthorized" | "outside-root" | "symlink" | "too-large" | "toctou"


def plan_injection(
    path: Path,
    rules: Sequence[Rule],
    *,
    authorize: Authorize,
    root: Path,
    allow_reseal: bool,
    max_bytes: int,
    max_lines: int,
) -> InjectPlan:
    """Decide whether injection is permitted. Never writes."""
    try:
        resolved = path.resolve()
    except OSError:
        return InjectPlan(path, False, "", "", "outside-root")

    # 1. Symlink refusal
    if path.is_symlink():
        return InjectPlan(path, False, "", "", "symlink")

    # 2. Root confinement
    if not _is_under(resolved, root):
        return InjectPlan(path, False, "", "", "outside-root")

    # 3. Authorization
    if not authorize.allows(resolved):
        return InjectPlan(path, False, "", "", "unauthorized")

    # 4. Size / line ceilings
    try:
        st = resolved.stat()
    except OSError:
        return InjectPlan(path, False, "", "", "outside-root")
    if not stat.S_ISREG(st.st_mode):
        return InjectPlan(path, False, "", "", "symlink")
    if st.st_size > max_bytes:
        return InjectPlan(path, False, "", "", "too-large")

    try:
        source = resolved.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return InjectPlan(path, False, "", "", "outside-root")
    if source.count("\n") > max_lines:
        return InjectPlan(path, False, "", "", "too-large")

    # 5. Parse + rules — poison gate
    try:
        tree = ast.parse(source, filename=str(resolved))
    except SyntaxError:
        return InjectPlan(path, False, "", "", "poison")

    ctx = RuleContext(str(resolved), source, tree, _parents(tree))
    for rule in rules:
        for _ in rule(tree, ctx):
            # First violation ⇒ poison. Do not enumerate further.
            return InjectPlan(path, False, "", "", "poison")

    # 6. Idempotency + reseal policy
    old_digest = find_seal_digest(source) or ""
    parts = split_header(source)
    new_digest = compute_seal(parts.recompose(), domain=SEAL_DOMAIN)
    if old_digest and old_digest != new_digest and not allow_reseal:
        return InjectPlan(path, False, old_digest, new_digest, "needs-reseal")
    if old_digest == new_digest:
        return InjectPlan(path, False, old_digest, new_digest, "noop")

    return InjectPlan(path, True, old_digest, new_digest, "ok")


def apply_injection(plan: InjectPlan, *, tag: str = SEAL_TAG_CLEAN) -> None:
    """Perform the write, guarded by a TOCTOU re-hash."""
    if not plan.changed:
        return
    resolved = plan.path.resolve()
    before = resolved.read_text(encoding="utf-8")
    parts = split_header(before)
    pre_hash = compute_seal(parts.recompose(), domain=SEAL_DOMAIN)
    if pre_hash != plan.new_digest:
        raise PoisonRefused(resolved, "TOCTOU: source changed between plan and apply")

    new_source = parts.recompose(build_seal_line(plan.new_digest, tag=tag) + "\n")
    resolved.write_text(new_source, encoding="utf-8")


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 7 — VERIFY (read-only)
# ═════════════════════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class VerifyResult:
    ok: bool
    expected: str
    found: str


def verify_seal(path: Path) -> VerifyResult:
    source = path.read_text(encoding="utf-8")
    found = find_seal_digest(source) or ""
    parts = split_header(source)
    expected = compute_seal(parts.recompose(), domain=SEAL_DOMAIN)
    return VerifyResult(ok=(found == expected), expected=expected, found=found)


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 8 — CONFIG
# ═════════════════════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class GuardConfig:
    rule_codes: Tuple[str, ...] = tuple(_RULES_BY_CODE.keys())

    @classmethod
    def from_yaml(cls, path: Path) -> "GuardConfig":
        if not HAS_YAML:
            raise RuntimeError("PyYAML required for --config; install pyyaml")
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        codes = tuple(raw.get("rules", cls().rule_codes))
        unknown = [c for c in codes if c not in _RULES_BY_CODE]
        if unknown:
            raise ValueError(f"unknown rule code(s): {', '.join(unknown)}")
        return cls(rule_codes=codes)

    def rules(self) -> Tuple[Rule, ...]:
        return tuple(_RULES_BY_CODE[c] for c in self.rule_codes)


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 9 — PARSING / WALKING
# ═════════════════════════════════════════════════════════════════════════════
def _parents(tree: ast.AST) -> Mapping[int, ast.AST]:
    parents: dict[int, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[id(child)] = parent
    return parents


def check_file(path: Path, rules: Sequence[Rule]) -> List[Finding]:
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return [Finding("IO", f"cannot read file: {e}", str(path), 0, 0, "File")]
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as e:
        return [Finding("SYNTAX", f"syntax error: {e.msg}", str(path),
                        e.lineno or 0, e.offset or 0, "SyntaxError")]
    ctx = RuleContext(str(path), source, tree, _parents(tree))
    findings: List[Finding] = []
    for rule in rules:
        findings.extend(rule(tree, ctx))
    return findings


def iter_python_files(targets: Sequence[str]) -> Iterator[Path]:
    for t in targets:
        p = Path(t)
        if p.is_dir():
            for f in sorted(p.rglob("*.py")):
                if any(part in SKIPPED_DIR_PARTS for part in f.parts):
                    continue
                yield f
        elif p.is_file():
            yield p
        else:
            print(f"warning: not found: {p}", file=sys.stderr)


# ═════════════════════════════════════════════════════════════════════════════
# SECTION 10 — CLI
# ═════════════════════════════════════════════════════════════════════════════
@dataclass(frozen=True)
class Command:
    targets: Sequence[str]
    json: bool
    quiet: bool
    config: Optional[str]
    inject_seal: bool
    apply: bool
    authorize: Sequence[str]
    authorize_file: Optional[str]
    root: Optional[str]
    reseal: bool
    verify_seal: bool
    max_bytes: int
    max_lines: int


def _parse_args(argv: Optional[Sequence[str]]) -> Command:
    ap = argparse.ArgumentParser(
        description="AST_guard: static AST rules + poison-guarded seal injection.")
    ap.add_argument("targets", nargs="+")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--config", default=None)
    ap.add_argument("--inject-seal", action="store_true",
                    help="plan seal injection (dry-run unless --apply)")
    ap.add_argument("--apply", action="store_true",
                    help="perform writes for --inject-seal")
    ap.add_argument("--authorize", action="append", default=[],
                    help="repeatable; explicit file path authorized for injection")
    ap.add_argument("--authorize-file", default=None,
                    help="file listing authorized paths (one per line, # comments)")
    ap.add_argument("--root", default=None,
                    help="confine writes to this root (default: git worktree or cwd)")
    ap.add_argument("--reseal", action="store_true",
                    help="allow overwriting an existing seal with a new digest")
    ap.add_argument("--verify-seal", action="store_true")
    ap.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    ap.add_argument("--max-lines", type=int, default=DEFAULT_MAX_LINES)
    ns = ap.parse_args(argv)
    return Command(
        targets=ns.targets, json=ns.json, quiet=ns.quiet, config=ns.config,
        inject_seal=ns.inject_seal, apply=ns.apply,
        authorize=ns.authorize, authorize_file=ns.authorize_file,
        root=ns.root, reseal=ns.reseal, verify_seal=ns.verify_seal,
        max_bytes=ns.max_bytes, max_lines=ns.max_lines,
    )


def _build_authorize(cmd: Command) -> Authorize:
    paths = list(cmd.authorize)
    if cmd.authorize_file:
        extra = Authorize.from_file(Path(cmd.authorize_file))
        return Authorize(frozenset(extra.allowed | Authorize.from_paths(paths).allowed))
    return Authorize.from_paths(paths)


def _render(findings: Sequence[Finding], plans: Sequence[InjectPlan],
            verifies: Sequence[dict], files_checked: int, quiet: bool) -> None:
    for v in findings:
        print(v.fmt())
    for p in plans:
        mark = {"ok": "🖋", "noop": "✓"}.get(p.reason, "🚫")
        old = p.old_digest[:16] or "—"
        new = p.new_digest[:16] or "—"
        print(f"{mark} {p.path}  reason={p.reason}  new={new}  old={old}")
    for r in verifies:
        mark = "✅" if r["ok"] else "❌"
        print(f"{mark} {r['file']}  expected={r['expected'][:16]}…  found={r['found'][:16] or '—'}")
    if not quiet:
        print(f"\n[{files_checked} file(s); "
              f"{len(findings)} violation(s); "
              f"{len(plans)} inject-plan(s); "
              f"{len(verifies)} verify-op(s)]", file=sys.stderr)


def run(cmd: Command) -> int:
    try:
        config = GuardConfig.from_yaml(Path(cmd.config)) if cmd.config else GuardConfig()
    except (OSError, ValueError, RuntimeError) as e:
        print(f"config error: {e}", file=sys.stderr)
        return 2

    rules = config.rules()
    root = _resolve_root(cmd.root)
    authorize = _build_authorize(cmd)

    findings: List[Finding] = []
    plans: List[InjectPlan] = []
    verifies: List[dict] = []
    files_checked = 0
    seal_only = cmd.inject_seal or cmd.verify_seal

    for path in iter_python_files(cmd.targets):
        files_checked += 1

        if cmd.inject_seal:
            plan = plan_injection(
                path, rules,
                authorize=authorize, root=root,
                allow_reseal=cmd.reseal,
                max_bytes=cmd.max_bytes, max_lines=cmd.max_lines,
            )
            plans.append(plan)
            if cmd.apply and plan.reason == "ok":
                try:
                    apply_injection(plan)
                except PoisonRefused as e:
                    findings.append(Finding("POISON", e.reason, str(path), 0, 0, "InjectPlan"))
                    # Downgrade reason for reporting
                    plans[-1] = InjectPlan(plan.path, False, plan.old_digest,
                                           plan.new_digest, "toctou")

        if cmd.verify_seal:
            try:
                v = verify_seal(path)
                verifies.append({"file": str(path), "ok": v.ok,
                                 "expected": v.expected, "found": v.found})
            except OSError as e:
                findings.append(Finding("IO", f"seal verify failed: {e}",
                                        str(path), 0, 0, "File"))

        if not seal_only:
            findings.extend(check_file(path, rules))

    if cmd.json:
        print(json.dumps({
            "files_checked": files_checked,
            "violations": [asdict(v) for v in findings],
            "inject_plans": [{
                "path": str(p.path), "changed": p.changed,
                "old_digest": p.old_digest, "new_digest": p.new_digest,
                "reason": p.reason,
            } for p in plans],
            "verify_seal": verifies,
            "root": str(root),
            "authorized": sorted(str(p) for p in authorize.allowed),
        }, indent=2))
    else:
        _render(findings, plans, verifies, files_checked, cmd.quiet)

    # Exit codes
    if findings:
        return 1
    if any(p.reason not in ("ok", "noop") for p in plans):
        # Refused injections (poison, unauthorized, symlink, too-large, etc.)
        return 1
    if cmd.verify_seal and any(not r["ok"] for r in verifies):
        return 1
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    return run(_parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
