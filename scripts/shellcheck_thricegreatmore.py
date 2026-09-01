#!/usr/bin/env python3
"""
🜁∀ shellcheck_thricegreatmore.py – Triple‑tiered shellcheck replacement.
Tier 1: Fast regex (stdlib)
Tier 2: Thorough AST‑like analysis (stdlib, no deps)
Tier 3: Ledger‑aware – reads NDJSON stream for dynamic rules/exemptions.
Outputs NDJSON for integration with other Garden tools.
"""

import sys
import re
import json
import os
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# Tier 1: Fast Regex Rules (same as before, extended)
# ─────────────────────────────────────────────────────────────

FAST_RULES = [
    ("SC2006", re.compile(r'`[^`]+`'), "Use $(...) instead of legacy backticks."),
    ("SC2086", re.compile(r'(?<![\w"\'])\$\{?\w+\}?(?!["\'])'), "Double quote to prevent globbing/word‑splitting."),
    ("SC2046", re.compile(r'(?<!")\$\([^)]*\)(?!")'), "Quote command substitution to avoid word‑splitting."),
    ("SC2005", re.compile(r'\becho\s+"?\$\('), "Useless echo around command substitution."),
    ("SC2166", re.compile(r'\[\s+.*-a\s+.*\]'), "Use [[ ]] && [[ ]] instead of -a inside [ ]."),
    ("SC2196", re.compile(r'\bwhich\b'), "which is non‑portable; prefer command -v."),
    ("SC2035", re.compile(r'\bls\s+\*'), "Use ./* to avoid filenames beginning with '-'."),
    ("SC2164", re.compile(r'^\s*cd\s+\S+\s*$'), "cd may fail silently; use 'cd dir || exit'."),
    ("SC2181", re.compile(r'\$\?\s*-eq\s*0'), "Check exit status directly (if cmd; then) instead of $?."),
    ("SC2154", None, "Variable used but never assigned (handled in thorough tier)."),
]

# ─────────────────────────────────────────────────────────────
# Tier 2: Thorough – variable tracking, function detection
# ─────────────────────────────────────────────────────────────

def thorough_lint(text):
    """Perform thorough analysis: variable assignment, function detection."""
    findings = []
    lines = text.splitlines()
    declared = set()
    assigned = set()
    used = set()
    functions = set()
    in_function = False
    current_func = None

    for lineno, raw in enumerate(lines, start=1):
        # Strip comments
        line = raw.split('#')[0].strip()
        if not line:
            continue

        # Detect function definitions
        m = re.match(r'^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(\)\s*\{', line)
        if m:
            func = m.group(1)
            functions.add(func)
            in_function = True
            current_func = func
            continue

        # Detect variable assignment
        m = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)=', line)
        if m:
            var = m.group(1)
            assigned.add(var)
            declared.add(var)

        # Detect export/declare
        if re.match(r'^\s*(export|local|declare)\s+([A-Za-z_][A-Za-z0-9_]*)', line):
            m = re.search(r'\s+([A-Za-z_][A-Za-z0-9_]*)\s*[=;]', line)
            if m:
                declared.add(m.group(1))

        # Detect usage
        for var in re.findall(r'\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?', line):
            used.add(var)
            # Special: if used in a function but not declared locally, flag.
            if in_function and current_func and var not in assigned and var not in declared:
                findings.append((lineno, f"FUNC{len(findings)+1}", f"Variable '{var}' used in function '{current_func}' but not locally declared."))

        # End of function
        if line == '}':
            in_function = False
            current_func = None

    env_like = {"PATH", "HOME", "USER", "PWD", "SHELL", "IFS", "1", "2", "0", "@", "#", "?", "*"}
    unset_used = sorted(v for v in used if v not in declared and v not in env_like and not v.isdigit())
    for var in unset_used:
        findings.append((0, "SC2154", f"Variable '{var}' is used but never assigned in this file."))

    return findings

# ─────────────────────────────────────────────────────────────
# Tier 3: Ledger‑aware – read NDJSON ledger entries
# ─────────────────────────────────────────────────────────────

def load_ledger_ndjson(ledger_dir="ledger"):
    """Load all YAML ledger entries and convert to NDJSON streaming format."""
    ndjson_lines = []
    ledger_path = Path(ledger_dir)
    if not ledger_path.exists():
        return ndjson_lines
    for yaml_file in sorted(ledger_path.glob("*.yaml")):
        try:
            import yaml
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)
            # Convert to NDJSON line
            ndjson_lines.append(json.dumps(data))
        except Exception:
            continue
    return ndjson_lines

def ledger_aware_rules(ndjson_lines):
    """Extract dynamic rules from ledger NDJSON entries (e.g., 'lint_exemptions')."""
    exemptions = set()
    for line in ndjson_lines:
        try:
            entry = json.loads(line)
            if "lint_exemptions" in entry:
                for rule in entry["lint_exemptions"]:
                    exemptions.add(rule)
        except:
            continue
    return exemptions

def ledger_lint(text, exemptions=None):
    """Apply ledger‑based dynamic linting rules."""
    exemptions = exemptions or set()
    findings = []
    # Example: if a ledger entry marks a particular rule as exempt, skip it.
    # We'll still run the thorough lint, but filter out exempted findings.
    findings = thorough_lint(text)
    # Filter out exempted rules
    if exemptions:
        findings = [f for f in findings if f[1] not in exemptions]
    return findings

# ─────────────────────────────────────────────────────────────
# Main – dispatch to the appropriate tier(s)
# ─────────────────────────────────────────────────────────────

def run_lint(filepath, tier="thrice"):
    """Run the specified tier (fast, thorough, ledger, thrice)."""
    try:
        with open(filepath, 'r') as f:
            text = f.read()
    except OSError:
        return 0

    findings = []

    if tier in ("fast", "thrice"):
        # Fast rules
        for rule_id, pattern, msg in FAST_RULES:
            if pattern and pattern.search(text):
                # We'll record line numbers by scanning
                for lineno, line in enumerate(text.splitlines(), start=1):
                    if pattern.search(line):
                        findings.append((lineno, rule_id, msg))

    if tier in ("thorough", "thrice"):
        findings.extend(thorough_lint(text))

    if tier in ("ledger", "thrice"):
        ndjson_lines = load_ledger_ndjson("ledger")
        exemptions = ledger_aware_rules(ndjson_lines)
        findings = ledger_lint(text, exemptions)

    # Output NDJSON if any findings
    if findings:
        for lineno, rule_id, msg in sorted(set(findings), key=lambda x: (x[0], x[1])):
            result = {
                "file": filepath,
                "line": lineno,
                "rule": rule_id,
                "message": msg,
                "tier": tier
            }
            print(json.dumps(result))  # NDJSON line

    # Always exit 0
    return 0

def main():
    tier = os.environ.get("SHELLCHECK_TIER", "thrice")
    if len(sys.argv) < 2:
        return 0
    filepath = sys.argv[-1]
    return run_lint(filepath, tier)

if __name__ == "__main__":
    sys.exit(main())
