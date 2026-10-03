#!/usr/bin/env python3
"""
Canary probe — Clarke Yoursa Tee
Thin, offline, no servers, no visualizations.
Checks:
  1. artifact line count == 2545
  2. artifact compiles
  3. no forbidden 0.0.0.0 bind in this probe
  4. garden_eternal_rules_verify() passes
"""

import sys

ARTIFACT_PATH = "artifacts/iphone12_quantum_terminal.py"
EXPECTED_LINES = 2545


def check_line_count() -> bool:
    with open(ARTIFACT_PATH, "r", encoding="utf-8") as f:
        lines = sum(1 for _ in f)
    if lines != EXPECTED_LINES:
        print(f"❌ Line count {lines} != {EXPECTED_LINES}")
        return False
    print(f"✅ Line count {lines} == {EXPECTED_LINES}")
    return True


def check_compile() -> bool:
    try:
        import py_compile
        py_compile.compile(ARTIFACT_PATH, doraise=True)
        print("✅ Artifact compiles")
        return True
    except py_compile.PyCompileError as e:
        print(f"❌ Compile error: {e}")
        return False


def check_bind_contract() -> bool:
    with open(__file__, "r", encoding="utf-8") as f:
        probe_source = f.read()
    if "HTTPServer(('0.0.0.0'" in probe_source:
        print("❌ Forbidden bind found in probe")
        return False
    print("✅ Probe binds clean")
    return True


def check_garden_rules() -> bool:
    try:
        from garden_surgery.garden_eternal_rules import garden_eternal_rules_verify
        result = garden_eternal_rules_verify()
        if result["ontological_equation"]["status"] != "PASS":
            print("❌ Garden rules failed")
            return False
        print("✅ Garden rules PASS")
        return True
    except Exception as e:
        print(f"❌ Garden rules exception: {e}")
        return False


def main():
    ok = True
    ok &= check_line_count()
    ok &= check_compile()
    ok &= check_bind_contract()
    ok &= check_garden_rules()
    if ok:
        print("✅ Canary probe complete: all checks passed")
        sys.exit(0)
    else:
        print("❌ Canary probe failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
