#!/usr/bin/env python3
"""Optional PyTorch wire for hexstrike metrics.

torch==1.8.1+cpu is not used. That wheel is for CPython 3.6-3.9.
If torch imports, the six metrics become a 1-d float tensor.
If it does not, the stdlib numbers are printed and nothing is installed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

KEYS = ("files_seen", "parsed", "unparsed", "drafts_skipped", "sealed", "findings")


def main() -> int:
    raw = Path(sys.argv[1]).read_text() if len(sys.argv) > 1 else sys.stdin.read()
    data = json.loads(raw)
    metrics = data["metrics"] if isinstance(data, dict) and "metrics" in data else data
    row = [float(metrics.get(key, 0)) for key in KEYS]
    try:
        import torch
    except ImportError:
        print(json.dumps({
            "torch": "absent",
            "python": ".".join(str(n) for n in sys.version_info[:2]),
            "keys": list(KEYS),
            "values": row,
            "install": "not run; 1.8.1+cpu is the wrong wheel for 3.10",
        }, indent=2))
        return 0
    tensor = torch.tensor(row, dtype=torch.float32)
    print(json.dumps({
        "torch": torch.__version__,
        "shape": list(tensor.shape),
        "keys": list(KEYS),
        "values": tensor.tolist(),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
