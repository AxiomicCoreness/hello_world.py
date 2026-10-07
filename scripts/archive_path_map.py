#!/usr/bin/env python3
"""Map kernel/ to op_kernel/. Does not copy the Ascend plugin.

Longer prefix wins: kernel/arch35/ -> op_kernel/arch35/, then kernel/ -> op_kernel/.
op_host/ stays op_host/. Other paths are unchanged.
"""

from __future__ import annotations

import sys

MAP = (
    ("kernel/arch35/", "op_kernel/arch35/"),
    ("kernel/", "op_kernel/"),
    ("op_host/", "op_host/"),
)


def map_path(rel: str) -> str:
    rel = rel.replace("\\", "/").lstrip("./")
    for src, dst in MAP:
        if rel.startswith(src):
            return dst + rel[len(src):]
    return rel


def main() -> int:
    paths = sys.argv[1:] or ["kernel/arch35/foo.cpp", "kernel/bar.cpp", "op_host/x.cpp", "docs/a.md"]
    for path in paths:
        print(f"{path} -> {map_path(path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
