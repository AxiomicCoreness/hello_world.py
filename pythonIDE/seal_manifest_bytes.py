#!/usr/bin/env python3
"""External byte seal for pythonIDE/integration_manifest.py.

This file is not the subject. It hashes the subject file bytes, which
include the executable code. The subject's BODY_SEAL and AST_HEAD_SEAL
do not cover that range.

Recorded digest is SHA3-256 of blob 72ba21ef87d001e3e0b7eda70dbb7c35b6ee4ef7
at commit dd69eb8b028822d2b15c94db98fb93786b1c78f9.
A later edit of the subject changes this digest. That is the point.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

SUBJECT = "pythonIDE/integration_manifest.py"
SUBJECT_COMMIT = "dd69eb8b028822d2b15c94db98fb93786b1c78f9"
SUBJECT_BLOB = "72ba21ef87d001e3e0b7eda70dbb7c35b6ee4ef7"
FILE_SHA3_256 = "8f3e4eb6434d3fc079491c7763b454c15d00095a928b934f1b01e311862859e1"


def file_digest(path: Path) -> str:
    return hashlib.sha3_256(path.read_bytes()).hexdigest()


def main() -> int:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else SUBJECT)
    digest = file_digest(path)
    ok = digest == FILE_SHA3_256
    print(json.dumps({
        "tool": "pythonIDE/seal_manifest_bytes.py",
        "subject": str(path),
        "subject_commit": SUBJECT_COMMIT,
        "subject_blob": SUBJECT_BLOB,
        "file_sha3_256": digest,
        "recorded": FILE_SHA3_256,
        "outcome": "ok" if ok else "file_mismatch",
        "covers": "file bytes, including executable code",
    }, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
