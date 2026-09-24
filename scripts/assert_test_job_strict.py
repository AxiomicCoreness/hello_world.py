#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
assert_test_job_strict.py — verify that a workflow's `test` job is strict.

Strict means:
  - no job-level continue-on-error
  - no step-level continue-on-error
  - no shell construct that masks a failing command

Exit codes:
  0  the job is strict
  1  one or more violations found
  2  workflow missing, job missing, or YAML unparseable

Blind spots, stated plainly:
  - The masking-pattern set catches the common forms (`|| true`,
    `|| exit 0`, trailing `; true`, trailing `|| :`). It does not
    parse shell grammar. A construction that masks failure in a way
    not listed here will pass this check. If you add a new form to
    the codebase, add its pattern here at the same time.
  - The check is job-local. It does not know whether the job's
    `if:` condition is always false, nor whether another job's
    failure matters.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

WORKFLOW = Path(".github/workflows/master-equation-ci.yml")
JOB = "test"

# Trailing masking constructs. Each must be the last effective thing
# on its line to mask the whole step's exit code, so we anchor to EOL.
MASKING_PATTERNS = (
    re.compile(r"\|\|\s*true\s*$"),
    re.compile(r"\|\|\s*exit\s+0\s*$"),
    re.compile(r";\s*true\s*$"),
    re.compile(r";\s*:\s*$"),
    re.compile(r"\|\|\s*:\s*$"),
)


def is_truthy(v) -> bool:
    """Match GitHub's continue-on-error semantics: true/'true'/'True' are true,
    'false'/'False'/'0'/'' and None are false. Anything else is a bool()."""
    if v is None:
        return False
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() not in ("", "false", "0", "no")
    return bool(v)


def check_job_continue_on_error(job: dict) -> list[str]:
    if is_truthy(job.get("continue-on-error")):
        return ["job-level continue-on-error is truthy"]
    return []


def check_steps(job: dict) -> list[str]:
    problems: list[str] = []
    for i, step in enumerate(job.get("steps") or []):
        name = step.get("name") or f"<step {i}>"

        if is_truthy(step.get("continue-on-error")):
            problems.append(f"step '{name}': continue-on-error is truthy")

        run = step.get("run")
        if not isinstance(run, str):
            continue

        # Check the last non-empty line of the run block only. A trailing
        # masking construct on an inner line cannot affect the step's
        # overall exit code, because the outer shell continues.
        lines = [ln.rstrip() for ln in run.splitlines() if ln.strip()]
        if not lines:
            continue
        last = lines[-1]
        for pat in MASKING_PATTERNS:
            if pat.search(last):
                problems.append(
                    f"step '{name}': last line masks failure ({pat.pattern!r})"
                )
                break

    return problems


def main() -> int:
    if not WORKFLOW.exists():
        print(f"::error::{WORKFLOW} not found", file=sys.stderr)
        return 2

    try:
        wf = yaml.safe_load(WORKFLOW.read_text())
    except yaml.YAMLError as e:
        print(f"::error::{WORKFLOW} failed to parse: {e}", file=sys.stderr)
        return 2

    jobs = (wf or {}).get("jobs") or {}
    if JOB not in jobs:
        print(f"::error::job '{JOB}' not found in {WORKFLOW}", file=sys.stderr)
        return 2

    job = jobs[JOB]
    problems = check_job_continue_on_error(job) + check_steps(job)

    if problems:
        for p in problems:
            print(f"FAIL: {p}")
        return 1

    print(f"OK: job '{JOB}' is strict")
    return 0


if __name__ == "__main__":
    sys.exit(main())
