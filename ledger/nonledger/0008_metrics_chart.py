#!/usr/bin/env python3
"""Stdlib chart for hexstrike metrics. Matplotlib is not installed and not required."""

from __future__ import annotations

import json
import sys
from pathlib import Path

KEYS = ("files_seen", "parsed", "unparsed", "drafts_skipped", "sealed", "findings")


def bars(metrics: dict) -> str:
    values = [int(metrics.get(key, 0)) for key in KEYS]
    top = max(values) or 1
    width, height, pad = 480, 180, 28
    slot = (width - 2 * pad) / len(KEYS)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="#111"/>',
    ]
    for i, (key, value) in enumerate(zip(KEYS, values)):
        h = int(100 * value / top)
        x = pad + i * slot + 8
        y = 120 - h
        parts.append(f'<rect x="{x:.0f}" y="{y}" width="36" height="{h}" fill="#c9a227"/>')
        parts.append(
            f'<text x="{x:.0f}" y="140" fill="#ddd" font-size="10">{key}</text>'
        )
        parts.append(f'<text x="{x:.0f}" y="{y - 4}" fill="#ddd" font-size="10">{value}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> int:
    raw = Path(sys.argv[1]).read_text() if len(sys.argv) > 1 else sys.stdin.read()
    data = json.loads(raw)
    metrics = data.get("metrics", data)
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("metrics.svg")
    out.write_text(bars(metrics))
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
