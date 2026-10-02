#!/usr/bin/env python3
"""External byte seal for pythonIDE/integration_manifest.py.

This file is not the subject. It is the floor of this chain: nothing
here seals this tool. Its authority is the review of commit 11e535c3
and of whatever commit replaces it. Editing this file to print a
constant would not move the subject seals.

Which bytes: git cat-file blob SUBJECT_BLOB. That is the committed
object, LF as stored. open(path).read() is a working-tree read and is
rejected. CRLF checkout bytes are a different digest.

Which Python: hashlib.sha3_256 is the hash. Interpreter pin below is
the version that produced the recorded digest, not a claim that every
interpreter will agree on ast.get_docstring. This tool does not call
ast.get_docstring.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys

SUBJECT = "pythonIDE/integration_manifest.py"
SUBJECT_COMMIT = "dd69eb8b028822d2b15c94db98fb93786b1c78f9"
SUBJECT_BLOB = "72ba21ef87d001e3e0b7eda70dbb7c35b6ee4ef7"
FILE_SHA3_256 = "8f3e4eb6434d3fc079491c7763b454c15d00095a928b934f1b01e311862859e1"
INTERPRETER = "3.10.21 (main, Sep 19 2026, 01:08:03) [GCC 12.2.0]"


def committed_blob() -> bytes:
    proc = subprocess.run(
        ["git", "cat-file", "blob", SUBJECT_BLOB],
        capture_output=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.decode("utf-8", "replace").strip() or "git cat-file failed")
    return proc.stdout


def main() -> int:
    if len(sys.argv) > 1:
        print(json.dumps({
            "outcome": "rejected",
            "reason": "path arguments are working-tree reads; use git cat-file blob",
        }, indent=2))
        return 2
    try:
        raw = committed_blob()
        source = "git cat-file blob"
    except (OSError, RuntimeError) as exc:
        print(json.dumps({
            "outcome": "unread",
            "reason": str(exc),
            "recorded": FILE_SHA3_256,
            "subject_blob": SUBJECT_BLOB,
        }, indent=2))
        return 2
    digest = hashlib.sha3_256(raw).hexdigest()
    ok = digest == FILE_SHA3_256
    print(json.dumps({
        "tool": "pythonIDE/seal_manifest_bytes.py",
        "source": source,
        "subject": SUBJECT,
        "subject_commit": SUBJECT_COMMIT,
        "subject_blob": SUBJECT_BLOB,
        "file_sha3_256": digest,
        "recorded": FILE_SHA3_256,
        "interpreter_pin": INTERPRETER,
        "interpreter_now": sys.version,
        "outcome": "ok" if ok else "file_mismatch",
        "covers": "committed blob bytes, including executable code",
        "floor": "this tool is unsealed",
    }, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
