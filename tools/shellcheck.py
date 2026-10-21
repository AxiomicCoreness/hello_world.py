#!/usr/bin/env python3
"""
shellcheck.py — Clarke Yoursa Tee
Pure Python shell/YAML linter, stdlib-only. No numpy/yaml/pip deps.
Runs under PythonIDE on A14 Bionic. Performs real shell-script static
checks; falls back to basic parse check for YAML. Always exits 0 to
satisfy the VS Code extension.

Corrections applied:
  - shebang regex now accepts #!/usr/bin/env <shell>
  - SC1000 placeholder removed from _RULES (dead code)
  - six additional rules: SC2155 SC2162 SC2016 SC2015 SC2048 SC2115
  - # shellcheck disable=... directive support
  - YAML path prints a one-line confirmation when clean (YAML001/YAML002)
"""
import sys
import os
import re

# --------------------------------------------------------------------
# Rule table: (id, compiled_pattern, message)
# Patterns are line-local (no AST) — zero deps, fast, adequate signal
# for an editor squiggle.
#
# Rules whose match must see the raw line (quotes intact) are listed in
# _RAW_RULES; all others are applied against quote-scrubbed text.
# --------------------------------------------------------------------

_RULES = [
    ("SC2006", re.compile(r'`[^`]+`'),
        "Use $(...) instead of legacy backticks."),
    ("SC2086", re.compile(r'(?<![\w\"\'])\$\{?\w+\}?(?![\"\'])'),
        "Double quote to prevent globbing/word-splitting."),
    ("SC2046", re.compile(r'(?<!")\$\([^)]*\)(?!")'),
        "Quote command substitution to avoid word-splitting."),
    ("SC2005", re.compile(r'\becho\s+"?\$\('),
        "Useless echo around command substitution."),
    ("SC2166", re.compile(r'\[\s+.*-a\s+.*\]'),
        "Use [[ ]] && [[ ]] instead of -a inside [ ]."),
    ("SC2196", re.compile(r'\bwhich\b'),
        "which is non-portable; prefer command -v."),
    ("SC2035", re.compile(r'\bls\s+\*'),
        "Use ./* to avoid filenames beginning with '-'."),
    ("SC2164", re.compile(r'^\s*cd\s+\S+\s*$'),
        "cd may fail silently; use 'cd dir || exit'."),
    ("SC2181", re.compile(r'\$\?\s*-eq\s*0'),
        "Check exit status directly (if cmd; then) instead of $?."),
    # ---- additions ----
    ("SC2155", re.compile(r'^\s*(?:local|export|declare)\s+\w+\s*=\s*\$\(.*\)'),
        "Declare and assign separately to preserve command exit code."),
    ("SC2162", re.compile(r'\bread\b(?!\s+-[a-zA-Z]*r)'),
        "read without -r will mangle backslashes."),
    ("SC2015", re.compile(r'&&.*\|\|'),
        "A && B || C is not if-then-else; use an if statement."),
    # ---- raw-line rules (see _RAW_RULES) ----
    ("SC2016", re.compile(r"'[^']*\$[A-Za-z_][A-Za-z0-9_]*[^']*'"),
        "Expressions do not expand in single quotes."),
    ("SC2048", re.compile(r'(?<!")\$\*(?![A-Za-z0-9_])'),
        'Use "$@" to expand positional parameters correctly.'),
    ("SC2115", re.compile(r'\brm\s+-[a-zA-Z]*r[a-zA-Z]*f?\s+"\$[A-Za-z_]\w*/"'),
        'Use "${var:?}" to guard rm -rf on a possibly-empty variable.'),
]

# Rule ids that must run against the raw (unscrubbed) line.
_RAW_RULES = frozenset({"SC2006", "SC2166", "SC2196", "SC2035", "SC2164",
                        "SC2181", "SC2016", "SC2048", "SC2115"})

_QUOTE_EXEMPT = re.compile(r'^\s*#')
_DISABLE_RE = re.compile(r'^\s*#\s*shellcheck\s+disable=([A-Z0-9,]+)')


def _strip_quoted_spans(line):
    """Blank out content inside single/double quotes so already-quoted
    variables do not false-positive."""
    out = []
    i = 0
    in_squote = in_dquote = False
    while i < len(line):
        ch = line[i]
        if ch == "'" and not in_dquote:
            in_squote = not in_squote
            out.append(" ")
        elif ch == '"' and not in_squote:
            in_dquote = not in_dquote
            out.append(" ")
        elif in_squote or in_dquote:
            out.append(" ")
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def lint_shell_text(text, filepath):
    findings = []
    disabled = set()
    declared = set()
    used = set()

    for lineno, raw in enumerate(text.splitlines(), start=1):
        m = _DISABLE_RE.match(raw)
        if m:
            for code in m.group(1).split(","):
                disabled.add(code.strip())
            continue
        if _QUOTE_EXEMPT.match(raw):
            continue

        scrubbed = _strip_quoted_spans(raw)
        for rule_id, pattern, message in _RULES:
            if rule_id in disabled:
                continue
            haystack = raw if rule_id in _RAW_RULES else scrubbed
            if pattern.search(haystack):
                findings.append((lineno, rule_id, message))

        m = re.match(r'^\s*([A-Za-z_][A-Za-z0-9_]*)=', raw)
        if m:
            declared.add(m.group(1))
        for var in re.findall(r'\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?', raw):
            used.add(var)

    env_like = {"PATH", "HOME", "USER", "PWD", "SHELL", "IFS", "1", "2",
                "0", "@", "#", "?", "*"}
    if "SC2154" not in disabled:
        unset_used = sorted(v for v in used
                            if v not in declared and v not in env_like
                            and not v.isdigit())
        for var in unset_used:
            findings.append((0, "SC2154",
                f"Variable '{var}' is used but never assigned in this file."))

    return findings


def lint_yaml_text(text):
    findings = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        if '\t' in raw.split('#')[0]:
            findings.append((lineno, "YAML001",
                "Tabs are not allowed for indentation in YAML."))
        stripped = raw.rstrip('\n')
        if re.match(r'^\s*-\s*$', stripped):
            continue
        if re.search(r':\s+\S.*:\s*\S', stripped) and stripped.count(':') > 1 \
                and '"' not in stripped and "'" not in stripped:
            findings.append((lineno, "YAML002",
                "Multiple ':' on one line — check for unquoted mapping value."))
    return findings


def format_findings(filepath, findings):
    out = []
    for lineno, rule_id, message in sorted(findings, key=lambda f: (f[0], f[1])):
        loc = f"{filepath}:{lineno}" if lineno else filepath
        out.append(f"{loc}: {rule_id}: {message}")
    return "\n".join(out)


def run_lint(filepath):
    if not os.path.exists(filepath):
        return 0
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except OSError:
        return 0

    if filepath.endswith(('.yaml', '.yml')):
        findings = lint_yaml_text(content)
        if findings:
            sys.stderr.write(format_findings(filepath, findings) + "\n")
        else:
            sys.stdout.write(f"{filepath}: YAML001/YAML002 clean\n")
    elif filepath.endswith(('.sh', '.bash')) or content.startswith('#!'):
        findings = lint_shell_text(content, filepath)
        if findings:
            sys.stderr.write(format_findings(filepath, findings) + "\n")
    else:
        return 0

    return 0


def main():
    if len(sys.argv) < 2:
        return 0
    filepath = sys.argv[-1]
    return run_lint(filepath)


if __name__ == "__main__":
    sys.exit(main())

# ci-touch: 2026-10-21T15:33Z
