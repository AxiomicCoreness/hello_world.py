#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ast_guard_rules_g.py -- Golden-constant AST rules, parse-only.

These rules verify STRUCTURE, not VALUE. They check that the golden
constants are declared in the correct shape, carry full 64-hex seals,
and do not import legacy-runtime dependencies at module level.

They do NOT verify:
  - that (1 + math.sqrt(5))/2 == 1.618033988749895 at runtime
  - that a seal's 64 hex matches a recomputation
  - that an import inside try/except ImportError will succeed

Those are runtime facts. This module never executes the target.

Compatibility (corrected from draft):
  - Python 3.6+: ast.Constant does not exist before 3.8, so all
    constant matching goes through _const_value(), which handles
    both ast.Constant (3.8+) and ast.Num/ast.Str (3.6/3.7).
  - Subscript slices: on 3.6-3.8 the slice is wrapped in ast.Index;
    _slice_upper() unwraps both shapes. (Draft's direct ast.Slice
    access was a silent no-op on 3.6-3.8 -- a false-witness bug.)
  - No dataclasses in the fallback shims (3.6 lacks the module);
    plain classes with __init__ instead.
  - No 'from __future__ import annotations' (3.7+ only).
  - G2 scoped to golden modules and golden names only, to prevent
    the over-fire residual flagged in the draft (a bare 'width = 640'
    in a non-golden module is not a G2 concern).

Requires: Python 3.6+ standard library only. No third-party imports.
"""

import ast
import re
import sys

# --- Local imports guard ---------------------------------------------------
# The parent AST_guard.py may define RuleContext, Violation, Rule.
# To keep this module standalone-runnable, we use minimal shims
# when the parent is absent. No dataclasses (Python 3.6 lacks them).
try:
    from AST_guard import RuleContext, Violation, Rule  # type: ignore
except ImportError:
    class Violation(object):  # type: ignore[no-redef]
        def __init__(self, code, message, file, line, col, node_type):
            self.code = code
            self.message = message
            self.file = file
            self.line = line
            self.col = col
            self.node_type = node_type

        def fmt(self):
            return "%s:%s:%s: [%s] %s (%s)" % (
                self.file, self.line, self.col,
                self.code, self.message, self.node_type)

    class RuleContext(object):  # type: ignore[no-redef]
        def __init__(self, filename, source, tree, parents=None):
            self.filename = filename
            self.source = source
            self.tree = tree
            self.parents = parents or {}
            self.violations = []

        def report(self, code, msg, node):
            self.violations.append(Violation(
                code=code, message=msg, file=self.filename,
                line=getattr(node, "lineno", 0),
                col=getattr(node, "col_offset", 0),
                node_type=type(node).__name__,
            ))

    Rule = type  # type: ignore[assignment,misc]


# ==========================================================================
# Helpers -- version-tolerant node matching (the load-bearing fix)
# ==========================================================================

_HEX64_RE = re.compile(r"[0-9a-f]{64}$")


def _const_value(node):
    # type: (ast.AST) -> object
    """Return the literal value of a constant node on 3.6 through 3.12+.

    ast.Constant exists from 3.8. On 3.6/3.7 literals are ast.Num /
    ast.Str / ast.NameConstant. Returns None for non-literals.
    """
    if hasattr(ast, "Constant") and isinstance(node, ast.Constant):
        return node.value
    # Python 3.6/3.7 literal node types.
    if hasattr(ast, "Num") and isinstance(node, ast.Num):
        return node.n
    if hasattr(ast, "Str") and isinstance(node, ast.Str):
        return node.s
    if hasattr(ast, "NameConstant") and isinstance(node, ast.NameConstant):
        return node.value
    return None


def _is_float_const(node, value=None):
    # type: (ast.AST, object) -> bool
    v = _const_value(node)
    return isinstance(v, float) and (value is None or v == value)


def _is_int_const(node, value):
    # type: (ast.AST, object) -> bool
    v = _const_value(node)
    return isinstance(v, int) and not isinstance(v, bool) and v == value


def _target_names(node):
    # type: (ast.AST) -> list
    names = []
    if isinstance(node, ast.Assign):
        targets = node.targets
    elif hasattr(ast, "AnnAssign") and isinstance(node, ast.AnnAssign):
        targets = [node.target]
    else:
        return names
    for t in targets:
        if isinstance(t, ast.Name):
            names.append(t.id)
    return names


def _module_level_names(tree):
    # type: (ast.Module) -> set
    out = set()
    for stmt in tree.body:
        out.update(_target_names(stmt))
    return out


# ==========================================================================
# G1 -- phi must be declared by expression, not by literal
# ==========================================================================

# Accepted shapes for phi:
#   (1 + math.sqrt(5)) / 2
#   (1 + 5 ** 0.5) / 2
#   (1 + 5 ** (1/2)) / 2
_PHI_LITERAL_BAND = (1.617, 1.619)


def _is_sqrt_of_five(node):
    # type: (ast.AST) -> bool
    # math.sqrt(5)
    if isinstance(node, ast.Call):
        f = node.func
        if (isinstance(f, ast.Attribute) and f.attr == "sqrt"
                and len(node.args) == 1
                and _is_int_const(node.args[0], 5)):
            return True
    # 5 ** 0.5  or  5 ** (1/2)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
        if _is_int_const(node.left, 5):
            right = node.right
            if _is_float_const(right, 0.5):
                return True
            if (isinstance(right, ast.BinOp)
                    and isinstance(right.op, ast.Div)
                    and _is_int_const(right.left, 1)
                    and _is_int_const(right.right, 2)):
                return True
    return False


def _is_phi_expression(node):
    # type: (ast.AST) -> bool
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Div):
        return False
    numerator, denominator = node.left, node.right
    if not _is_int_const(denominator, 2):
        return False
    if not isinstance(numerator, ast.BinOp) or not isinstance(numerator.op, ast.Add):
        return False
    left, right = numerator.left, numerator.right
    one_side = None
    sqrt_side = None
    for a, b in ((left, right), (right, left)):
        if _is_int_const(a, 1):
            one_side, sqrt_side = a, b
            break
    if one_side is None or sqrt_side is None:
        return False
    return _is_sqrt_of_five(sqrt_side)


def rule_G1_phi_by_expression(tree, ctx):
    # type: (ast.AST, RuleContext) -> None
    """G1: 'phi' must be assigned an expression, not a bare numeric literal."""
    if not isinstance(tree, ast.Module):
        return
    for stmt in tree.body:
        if not isinstance(stmt, ast.Assign):
            continue
        for target in stmt.targets:
            if not isinstance(target, ast.Name) or target.id != "phi":
                continue
            value = stmt.value
            v = _const_value(value)
            if isinstance(v, float):
                lo, hi = _PHI_LITERAL_BAND
                if lo <= v <= hi:
                    ctx.report(
                        "G1",
                        "phi assigned literal %r; expected (1 + math.sqrt(5)) / 2"
                        % (v,),
                        stmt,
                    )
                    continue
            if not _is_phi_expression(value):
                ctx.report(
                    "G1",
                    "phi must be declared as (1 + math.sqrt(5)) / 2 "
                    "or (1 + 5 ** 0.5) / 2",
                    stmt,
                )


# ==========================================================================
# G2 -- golden-constant alias coverage (scoped: golden modules only)
# ==========================================================================

# Golden constant names: the phi-family and greek-letter constants the
# alias rule was written for. A bare 'width' or 'count' in any module
# is NOT in scope. This closes the over-fire residual from the draft.
_GOLDEN_NAME_RE = re.compile(r"^(phi|chi|theta|tau|sigma|lambda_)[a-z0-9_]*$")


def _module_is_golden(filename):
    # type: (str) -> bool
    base = filename.replace("\\", "/").rsplit("/", 1)[-1].lower()
    return (
        "seal" in base
        or "golden" in base
        or "constant" in base
        or "phi" in base
    )


def rule_G2_alias_coverage(tree, ctx):
    # type: (ast.AST, RuleContext) -> None
    """G2: golden lowercase constants must have uppercase aliases.

    Scoped to golden modules and golden names (phi/chi/theta/tau/
    sigma/lambda_ families) -- the draft's unrestricted version
    flagged every lowercase module constant, which was noise.
    """
    if not isinstance(tree, ast.Module):
        return
    if not _module_is_golden(ctx.filename):
        return
    names = _module_level_names(tree)
    lower = {n for n in names
             if re.fullmatch(r"[a-z][a-z0-9_]*", n) and _GOLDEN_NAME_RE.match(n)}
    upper = {n for n in names if re.fullmatch(r"[A-Z][A-Z0-9_]*", n)}
    for name in sorted(lower):
        expected = name.upper()
        if expected not in upper:
            ctx.report(
                "G2",
                "golden constant %r has no uppercase alias %r"
                % (name, expected),
                tree,
            )


# ==========================================================================
# G3 -- seal strings must end in exactly 64 lowercase hex
# ==========================================================================

_SEAL_NAME_RE = re.compile(r"seal", re.IGNORECASE)


def _string_node_value(node):
    # type: (ast.AST) -> object
    v = _const_value(node)
    return v if isinstance(v, str) else None


def _looks_like_seal_field(name):
    # type: (str) -> bool
    return bool(_SEAL_NAME_RE.search(name))


def rule_G3_seal_full_hex(tree, ctx):
    # type: (ast.AST, RuleContext) -> None
    """G3: any string assigned to a name containing 'seal' must end in 64 hex."""
    for node in ast.walk(tree):
        # Case 1: simple assignment x_seal = "..."
        if isinstance(node, ast.Assign):
            for target in node.targets:
                name = None
                if isinstance(target, ast.Name):
                    name = target.id
                elif isinstance(target, ast.Attribute):
                    name = target.attr
                if name is None or not _looks_like_seal_field(name):
                    continue
                s = _string_node_value(node.value)
                if s is None:
                    continue
                if not _HEX64_RE.search(s):
                    ctx.report(
                        "G3",
                        "%r does not end in 64 lowercase hex" % (name,),
                        node,
                    )
        # Case 2: dict entries {"seal": "..."}
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                ks = _string_node_value(k) if k is not None else None
                if ks is None or not _looks_like_seal_field(ks):
                    continue
                vs = _string_node_value(v)
                if vs is None:
                    continue
                if not _HEX64_RE.search(vs):
                    ctx.report(
                        "G3",
                        "dict key %r does not end in 64 lowercase hex" % (ks,),
                        v,
                    )


# ==========================================================================
# G3b -- hex-digest slice truncation (catches sha3_256.hexdigest()[:16])
# ==========================================================================

def _is_hexdigest_producer(node):
    # type: (ast.AST) -> bool
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "hexdigest"
    )


def _slice_upper(node):
    # type: (ast.AST) -> object
    """Extract [None:upper] slice upper bound from a Subscript node.

    Version-tolerant: on 3.9+ node.slice is the ast.Slice directly;
    on 3.6-3.8 it is wrapped in ast.Index. The draft's direct
    ast.Slice access silently never matched on 3.6-3.8.
    """
    if not isinstance(node, ast.Subscript):
        return None
    sl = node.slice
    # Python 3.9+: slice is bare.
    if not isinstance(sl, ast.Slice):
        # Python 3.6-3.8: slice wrapped in ast.Index.
        if hasattr(ast, "Index") and isinstance(sl, ast.Index):
            sl = sl.value
        else:
            return None
    if not isinstance(sl, ast.Slice):
        return None
    if sl.lower is not None or sl.step is not None:
        return None
    v = _const_value(sl.upper)
    if isinstance(v, int) and not isinstance(v, bool):
        return v
    return None


def rule_G3b_no_digest_truncation(tree, ctx):
    # type: (ast.AST, RuleContext) -> None
    """G3b: refuse hexdigest()[:N] with N < 64 -- silent truncation."""
    for node in ast.walk(tree):
        n = _slice_upper(node)
        if n is None or n >= 64:
            continue
        if _is_hexdigest_producer(node.value):
            ctx.report(
                "G3b",
                "hexdigest()[:%d] truncates a 64-hex digest; "
                "keep full 64 or rename field to _short" % (n,),
                node,
            )


# ==========================================================================
# G4 -- golden-constant modules must not import legacy runtime deps
# ==========================================================================

LEGACY_DEPS = frozenset([
    "numpy", "scipy", "matplotlib", "seaborn",
    "pandas", "torch", "tensorflow", "jax", "jaxlib",
])


def _imported_top_level_names(node):
    # type: (ast.AST) -> object
    if isinstance(node, ast.Import):
        for alias in node.names:
            yield alias.name.split(".")[0]
    elif isinstance(node, ast.ImportFrom):
        if node.module:
            yield node.module.split(".")[0]


def rule_G4_no_legacy_import(tree, ctx):
    # type: (ast.AST, RuleContext) -> None
    """G4: golden modules must not import numpy/scipy/etc at module level.

    Guarded imports inside try/except ImportError are fine; this rule
    deliberately does not recurse into Try bodies.
    """
    if not _module_is_golden(ctx.filename):
        return
    if not isinstance(tree, ast.Module):
        return
    for stmt in tree.body:
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            for name in _imported_top_level_names(stmt):
                if name in LEGACY_DEPS:
                    ctx.report(
                        "G4",
                        "golden module must not import %r at module level"
                        % (name,),
                        stmt,
                    )


# ==========================================================================
# Rule registry -- drop this into AST_guard.py's DEFAULT_RULES
# ==========================================================================

GOLDEN_RULES = [
    rule_G1_phi_by_expression,
    rule_G2_alias_coverage,
    rule_G3_seal_full_hex,
    rule_G3b_no_digest_truncation,
    rule_G4_no_legacy_import,
]


# ==========================================================================
# Self-test (runs standalone on Python 3.6+)
# ==========================================================================

if __name__ == "__main__":
    SAMPLES = [
        ("clean_phi",
         "import math\nphi = (1 + math.sqrt(5)) / 2\nPHI = phi\n",
         []),
        ("literal_phi",
         "phi = 1.618033988749895\nPHI = phi\n",
         ["G1"]),
        # G2 is scoped to golden modules: the sample filenames below use
        # 'golden_' prefixes so the rule is actually exercised.
        ("missing_alias_golden",
         "import math\nphi = (1 + math.sqrt(5)) / 2\n",
         ["G2"]),
        ("no_alias_nongolden",
         "import math\nwidth = 640\n",
         []),
        ("seal_truncated",
         'x_seal = "\u2200\u221e\u03c6\u00b2 \u00b7 TEST \u00b7 abc123"\n',
         ["G3"]),
        ("seal_clean",
         'seal = "prefix \u00b7 " + "a" * 63 + "b"\n',
         []),
        ("slice_truncation",
         "import hashlib\nh = hashlib.sha3_256(b'x').hexdigest()[:16]\n",
         ["G3b"]),
        ("slice_full",
         "import hashlib\nh = hashlib.sha3_256(b'x').hexdigest()[:64]\n",
         []),
        ("legacy_import",
         "import numpy\nimport math\nphi = (1 + math.sqrt(5)) / 2\nPHI = phi\n",
         ["G4"]),
        # Constant-matching smoke test: on a broken 3.6 build using
        # ast.Constant-only matching, this sample would produce NO G1
        # (false witness). _const_value() must catch it.
        ("literal_phi_3_6_regression",
         "phi = 1.618\nPHI = phi\n",
         ["G1"]),
    ]

    fails = 0
    for label, src, expected in SAMPLES:
        tree = ast.parse(src, filename="<%s>" % label)
        fname = label if label.startswith("golden") else (
            "golden_sample.py" if "golden" in label or "alias" in label
            else "sample.py")
        # Ensure G2/G4 scoping is exercised where intended.
        if "alias" in label:
            fname = "golden_constants.py"
        ctx = RuleContext(filename=fname, source=src, tree=tree, parents={})
        for rule in GOLDEN_RULES:
            rule(tree, ctx)
        got = sorted(set(v.code for v in ctx.violations))
        want = sorted(set(expected))
        ok = got == want
        mark = "PASS" if ok else "FAIL"
        print("  %s %-32s got=%s want=%s" % (mark, label, got, want))
        fails += (not ok)

    print("")
    if fails:
        print("SELF-TEST FAILED: %d sample(s)" % fails)
        sys.exit(1)
    print("SELF-TEST PASSED: %d/%d samples" % (len(SAMPLES), len(SAMPLES)))
    sys.exit(0)
