#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""ledger_iso8601_gate.py — ISO 8601 timestamp gate for NEW ledger entries.

Rule (new entries only):
  Every ledger entry ADDED after the base commit must carry a `timestamp`, and
  `timestamp` plus every key ending in `_at` (at any depth) must be an
  ISO 8601 date-time with an explicit offset, `Z` or `+HH:MM` / `-HH:MM`,
  e.g. `2026-10-30T13:02:24-04:00`.

Legacy entries (everything not added after the base) are listed as
REPORT-ONLY and never fail the gate. The ledger is append-only: this tool
never writes to ledger/ or ledger.v2/.

"Added" means any of:
  * `git diff --name-status --diff-filter=A <base>...HEAD -- ledger ledger.v2`
  * staged additions (`git diff --cached --diff-filter=A`)
  * untracked files under ledger/ and ledger.v2/
Base: --base, else $LEDGER_ISO8601_BASE, else 778f4cf13e6a8ac2376e823b64eb84a59a245a4f.

Parsing: stdlib JSON, plus PyYAML (timestamps kept as raw strings) when it is
importable. If YAML entries must be read and PyYAML is missing, exit 2.

Exit: 0 pass, 1 a new entry violates the rule, 2 usage/IO (git, base,
missing PyYAML, a new entry that cannot be parsed).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple

DEFAULT_BASE = "778f4cf13e6a8ac2376e823b64eb84a59a245a4f"
BASE_ENV = "LEDGER_ISO8601_BASE"
LEDGER_DIRS = ("ledger", "ledger.v2")
ENTRY_SUFFIXES = (".yaml", ".yml", ".json")
REPO = Path(__file__).resolve().parent.parent

_ISO_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})$"
)


def is_iso8601_with_offset(value: object) -> bool:
    """True for e.g. 2026-10-30T13:02:24-04:00 or 2026-10-30T17:02:24Z."""
    if not isinstance(value, str) or not _ISO_RE.match(value):
        return False
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return dt.tzinfo is not None


class GateIOError(Exception):
    """Usage/IO problem -> exit 2."""


def _yaml_loader():
    """SafeLoader that keeps timestamps as the literal strings in the file."""
    import yaml  # type: ignore

    class _RawTimestampLoader(yaml.SafeLoader):
        pass

    _RawTimestampLoader.yaml_implicit_resolvers = {
        ch: [r for r in resolvers if r[0] != "tag:yaml.org,2002:timestamp"]
        for ch, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
    }
    return yaml, _RawTimestampLoader


def yaml_available() -> bool:
    try:
        import yaml  # type: ignore  # noqa: F401
    except ImportError:
        return False
    return True


def load_entry(path: Path) -> Tuple[Optional[dict], str]:
    """Return (mapping, "") or (None, reason)."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return None, f"read_error: {e}"
    if path.suffix == ".json":
        try:
            obj = json.loads(text)
        except json.JSONDecodeError as e:
            return None, f"parse_error: JSON: {e.msg}"
    else:
        try:
            yaml, loader = _yaml_loader()
        except ImportError:
            try:
                obj = json.loads(text)
            except json.JSONDecodeError:
                return None, "yaml_unavailable: PyYAML not importable and file is not JSON"
        else:
            try:
                obj = yaml.load(text, Loader=loader)  # noqa: S506 (SafeLoader subclass)
            except Exception as e:
                return None, "parse_error: YAML: " + " ".join(str(e).split())
    if not isinstance(obj, dict):
        return None, f"not_a_mapping: top level is {type(obj).__name__}"
    return obj, ""


def iter_time_fields(obj: object, prefix: str = "") -> Iterable[Tuple[str, object]]:
    """Yield (dotted_key, value) for `timestamp` and every `*_at` key, any depth."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            key = f"{prefix}.{k}" if prefix else str(k)
            if isinstance(k, str) and (k == "timestamp" or k.endswith("_at")):
                yield key, v
            if isinstance(v, (dict, list)):
                yield from iter_time_fields(v, key)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from iter_time_fields(v, f"{prefix}[{i}]")


@dataclass
class EntryResult:
    path: str
    new: bool
    parsed: bool
    problems: List[str] = field(default_factory=list)
    checked_fields: int = 0

    @property
    def ok(self) -> bool:
        return self.parsed and not self.problems


def check_entry(entry: dict) -> Tuple[int, List[str]]:
    problems: List[str] = []
    if "timestamp" not in entry:
        problems.append("missing required `timestamp`")
    n = 0
    for key, value in iter_time_fields(entry):
        n += 1
        if not is_iso8601_with_offset(value):
            problems.append(
                f"`{key}` = {value!r} is not ISO 8601 with offset "
                "(want e.g. 2026-10-30T13:02:24-04:00 or ...Z)"
            )
    return n, problems


def _git(repo: Path, *args: str) -> str:
    try:
        p = subprocess.run(
            ["git", "-c", "submodule.recurse=false", *args],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        raise GateIOError(f"git failed: {e}") from e
    if p.returncode != 0:
        raise GateIOError(f"git {' '.join(args)}: {p.stderr.strip()}")
    return p.stdout


def _is_entry(rel: str) -> bool:
    parts = rel.split("/")
    return parts[0] in LEDGER_DIRS and rel.endswith(ENTRY_SUFFIXES)


def added_entries(repo: Path, base: str) -> Set[str]:
    _git(repo, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}")
    added: Set[str] = set()
    out = _git(repo, "diff", "--name-status", "--diff-filter=A", f"{base}...HEAD", "--", *LEDGER_DIRS)
    out += _git(repo, "diff", "--cached", "--name-status", "--diff-filter=A", "--", *LEDGER_DIRS)
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0].startswith("A"):
            added.add(parts[-1])
    for line in _git(repo, "ls-files", "--others", "--exclude-standard", "--", *LEDGER_DIRS).splitlines():
        added.add(line.strip())
    return {p for p in added if _is_entry(p)}


def all_entries(repo: Path) -> List[str]:
    out: List[str] = []
    for d in LEDGER_DIRS:
        root = repo / d
        if not root.is_dir():
            continue
        for p in sorted(root.rglob("*")):
            if p.is_file() and p.suffix in ENTRY_SUFFIXES:
                out.append(p.relative_to(repo).as_posix())
    return out


def run_gate(repo: Path, base: str) -> dict:
    new = added_entries(repo, base)
    entries = sorted(set(all_entries(repo)) | new)
    results: List[EntryResult] = []
    for rel in entries:
        is_new = rel in new
        entry, reason = load_entry(repo / rel)
        r = EntryResult(rel, is_new, entry is not None)
        if entry is None:
            r.problems.append(reason)
        else:
            r.checked_fields, r.problems = check_entry(entry)
        results.append(r)
    yaml_missing = [r.path for r in results if not r.parsed and r.problems[0].startswith("yaml_unavailable")]
    if yaml_missing:
        raise GateIOError(
            "PyYAML is not importable in this interpreter "
            f"({sys.executable}; `python -I` hides the user site-packages) and "
            f"{len(yaml_missing)} YAML ledger entr(y/ies) cannot be read without it "
            f"(first: {yaml_missing[0]}); refusing to report a pass."
        )
    new_res = [r for r in results if r.new]
    legacy = [r for r in results if not r.new]
    return {
        "base": base,
        "new_entries": len(new_res),
        "new_failing": [vars(r) for r in new_res if r.parsed and r.problems],
        "new_unparsed": [vars(r) for r in new_res if not r.parsed],
        "new_passing": [r.path for r in new_res if r.ok],
        "legacy_entries": len(legacy),
        "legacy_ok": sum(1 for r in legacy if r.ok),
        "legacy_report_only": [vars(r) for r in legacy if not r.ok],
    }


def render(report: dict, verbose: bool) -> str:
    lines = [
        "ledger_iso8601_gate -- ISO 8601 with offset for new ledger entries",
        f"base             : {report['base']}",
        f"new entries      : {report['new_entries']}"
        f" (pass {len(report['new_passing'])}, fail {len(report['new_failing'])},"
        f" unparsed {len(report['new_unparsed'])})",
        f"legacy entries   : {report['legacy_entries']}"
        f" (ok {report['legacy_ok']}, report-only {len(report['legacy_report_only'])})",
        "=" * 64,
    ]
    for r in report["new_failing"] + report["new_unparsed"]:
        lines.append(f"  FAIL {r['path']}")
        for p in r["problems"]:
            lines.append(f"       {p}")
    if verbose:
        for r in report["legacy_report_only"]:
            lines.append(f"  REPORT-ONLY {r['path']}: {'; '.join(r['problems'])}")
    elif report["legacy_report_only"]:
        lines.append(
            f"  {len(report['legacy_report_only'])} legacy entries are report-only "
            "(use -v or --json to list them; they never fail the gate)"
        )
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", type=Path, default=REPO, help="repository root")
    ap.add_argument(
        "--base",
        default=None,
        help=f"base commit (default ${BASE_ENV} or {DEFAULT_BASE})",
    )
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args(argv)
    base = args.base or os.environ.get(BASE_ENV) or DEFAULT_BASE

    try:
        report = run_gate(args.repo.resolve(), base)
    except GateIOError as e:
        print(f"ledger_iso8601_gate: {e}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render(report, args.verbose))

    if report["new_unparsed"]:
        print(
            f"ledger_iso8601_gate: {len(report['new_unparsed'])} new entr(y/ies) "
            "could not be parsed",
            file=sys.stderr,
        )
        return 2
    return 1 if report["new_failing"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
