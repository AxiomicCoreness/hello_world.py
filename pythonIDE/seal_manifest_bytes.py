#!/usr/bin/env python3
"""External byte seal for pythonIDE/integration_manifest.py.

This file is the floor. Nothing in the subject seals it.

Which bytes, three different numbers:
  file_sha3_256 = SHA3-256(raw bytes from git cat-file blob).
    Content hash. Not a git OID. No CRLF conversion, no cleandoc.
  subject_blob = SHA-1(b"blob " + len + b"\0" + raw bytes).
    Git blob object ID, SHA-1 mode. 40 hex.
  A SHA-256 git OID is not used. This repo is not a SHA-256 repo.

Working-tree reads are rejected. A path argument exits 2.

docstring_mode is not computed here. The subject prints
docstring_mode=cleandoc via ast.get_docstring. That is a stdlib
contract, not a raw slice of the docstring.

produced_by_blob is the git blob ID of this file at HEAD. If the
working tree differs, the receipt says dirty. If the file is not in
git, the field is null.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

SUBJECT = "pythonIDE/integration_manifest.py"
SUBJECT_COMMIT = "15fc1c471892c5669146e4c800b8154f72593d3b"
SUBJECT_BLOB = "d957c0a84c6c96acabf5e6cd0d9e690f3c26938b"
FILE_SHA3_256 = "53196c0470792eecda7ed7b4adf9dbd354259be79211dc9654ecbad9900d6d96"
TOOL = "pythonIDE/seal_manifest_bytes.py"


def git_bytes(args: list[str]) -> bytes | None:
    proc = subprocess.run(["git", *args], capture_output=True)
    if proc.returncode != 0:
        return None
    return proc.stdout


def producer() -> dict:
    head = git_bytes(["rev-parse", f"HEAD:{TOOL}"])
    if head is None:
        return {"produced_by_blob": None, "producer_state": "untracked"}
    blob = head.decode().strip()
    raw = git_bytes(["cat-file", "blob", blob])
    here = Path(__file__).read_bytes()
    if raw is None:
        return {"produced_by_blob": blob, "producer_state": "unreadable"}
    if raw != here:
        return {"produced_by_blob": blob, "producer_state": "dirty"}
    return {"produced_by_blob": blob, "producer_state": "clean"}


def main() -> int:
    if len(sys.argv) > 1:
        print(json.dumps({"outcome": "rejected", "reason": "path arguments are working-tree reads"}, indent=2))
        return 2
    raw = git_bytes(["cat-file", "blob", SUBJECT_BLOB])
    who = producer()
    if raw is None:
        print(json.dumps({"outcome": "unread", "subject_blob": SUBJECT_BLOB, **who}, indent=2))
        return 2
    digest = hashlib.sha3_256(raw).hexdigest()
    oid = hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()
    ok = digest == FILE_SHA3_256 and oid == SUBJECT_BLOB
    print(json.dumps({
        "tool": TOOL,
        "source": "git cat-file blob",
        "hash_kind": "sha3_256 of raw blob bytes, not a git OID",
        "git_oid_kind": "sha1 blob header",
        "subject": SUBJECT,
        "subject_commit": SUBJECT_COMMIT,
        "subject_blob": oid,
        "file_sha3_256": digest,
        "recorded_file_sha3_256": FILE_SHA3_256,
        "docstring_mode": "cleandoc",
        "docstring_via": "ast.get_docstring in the subject, not this tool",
        "outcome": "ok" if ok else "file_mismatch",
        "floor": "this tool is unsealed",
        **who,
    }, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
