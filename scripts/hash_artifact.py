#!/usr/bin/env python3
"""scripts/hash_artifact.py — print SHA3-256 of a file (untruncated)."""
from __future__ import annotations

import hashlib
import pathlib
import sys

if len(sys.argv) < 2:
    print("usage: hash_artifact.py <path>", file=sys.stderr)
    sys.exit(2)

p = pathlib.Path(sys.argv[1])
if not p.is_file():
    sys.exit(0)  # absent → no output

print(hashlib.new("sha3_256", p.read_bytes()).hexdigest())
