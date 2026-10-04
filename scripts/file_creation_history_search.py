#!/usr/bin/env python3
"""Search a file's creation history for a version token.

Walks git follow-history from the introducing commit forward. Reports the
first commit whose blob contains the token, and the creation commit even
when the token is absent there. Stdlib only.
"""

import argparse
import subprocess
import sys


def git(args):
    result = subprocess.run(
        ["git", *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SystemExit(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def history(path):
    lines = git(
        ["log", "--follow", "--reverse", "--format=%H%x09%ci%x09%s", "--", path]
    ).splitlines()
    rows = []
    for line in lines:
        commit, when, subject = line.split("\t", 2)
        rows.append((commit, when, subject))
    return rows


def blob_has(commit, path, token):
    result = subprocess.run(
        ["git", "grep", "-n", "-F", "--", token, f"{commit}:{path}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 1:
        return []
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path")
    parser.add_argument("token")
    args = parser.parse_args()
    rows = history(args.path)
    if not rows:
        raise SystemExit(f"no creation history for {args.path}")
    first_commit, first_when, first_subject = rows[0]
    print(f"creation {first_commit[:12]} {first_when} {first_subject}")
    created_hits = blob_has(first_commit, args.path, args.token)
    print(f"token in creation version: {'yes' if created_hits else 'no'}")
    found = None
    for commit, when, subject in rows:
        hits = blob_has(commit, args.path, args.token)
        if hits:
            found = (commit, when, subject, hits)
            break
    if not found:
        print(f"token {args.token!r} not in any version of {args.path}")
        return 1
    commit, when, subject, hits = found
    print(f"first version {commit[:12]} {when} {subject}")
    for hit in hits[:8]:
        print(f"  {hit}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
