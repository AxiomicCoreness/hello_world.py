#!/usr/bin/env python3
"""pythonIDE object. One apply() call. stdlib only. No os._exit."""

from __future__ import annotations

import math


class StdlibCall:
    def apply(self, slot: int) -> dict:
        if not 0 <= slot < 24:
            raise ValueError("slot must be in 0..23")
        phi = (1.0 + math.sqrt(5.0)) / 2.0
        k = slot / 6.0
        return {"slot": slot, "k": k, "phi": phi, "exit": "SystemExit"}


def main() -> int:
    out = StdlibCall().apply(10)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
