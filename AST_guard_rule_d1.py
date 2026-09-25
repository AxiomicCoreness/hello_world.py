# AST_guard rule D1 — no_stale_module_paths
# Forged under ledger entry 8976 (witness 8975 → 8976).
# D1 forbids imports of pre-flattening module paths. Grep is discovery;
# D1 is enforcement. Stale imports fail CI before merge once D1 is wired
# into AST_guard.py DEFAULT_RULES (wiring deferred — defect D29 — because
# AST_guard.py bytes are missing from view; SHA e504dd1ead4cc60021c564615e6ca1e544b5972e).
# Pronoun-free per standing policy.

STALE_IMPORT_PREFIXES = (
    "celestial.strike_ix",
    "celestial.saturn_soul_cannon_strike_ix",
    "prometheus.trappist_metrics_draft",
)


def check_module(module_name, report, node):
    """Report a D1 violation when module_name matches a stale prefix."""
    for stale in STALE_IMPORT_PREFIXES:
        if module_name == stale or module_name.startswith(stale + "."):
            report(
                "D1",
                "stale module path '%s' (use the flattened form)" % module_name,
                node,
            )


def rule_D1_no_stale_module_paths(tree, ctx):
    """
    D1: forbid imports of the pre-flattening module paths.
    Add new pairs to STALE_IMPORT_PREFIXES as the tree evolves; remove
    entries only when the migration is complete and the rule can retire.
    """
    import ast

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                check_module(alias.name, ctx.report, node)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                check_module(node.module, ctx.report, node)


def _cli():
    """Standalone gate: python3 AST_guard_rule_d1.py FILE [FILE ...]
    Exit 0 = clean; exit 1 = stale imports found. Discovery grep is dead
    once this gate runs in CI."""
    import ast
    import sys

    class Ctx:
        def __init__(self):
            self.failures = []

        def report(self, rule_id, message, node):
            self.failures.append((rule_id, message, getattr(node, "lineno", 0)))

    total = 0
    for path in sys.argv[1:]:
        with open(path, "r", encoding="utf-8") as handle:
            tree = ast.parse(handle.read(), filename=path)
        ctx = Ctx()
        rule_D1_no_stale_module_paths(tree, ctx)
        for rule_id, message, lineno in ctx.failures:
            print("%s:%d: %s: %s" % (path, lineno, rule_id, message))
            total += 1
    if total:
        sys.exit(1)
    print("D1: no stale module paths")
    sys.exit(0)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        _cli()
