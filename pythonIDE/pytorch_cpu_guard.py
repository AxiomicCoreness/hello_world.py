#!/usr/bin/env python3
"""CPU PyTorch install guard.

The line

    pip install torch==1.8.1+cpu torchvision==0.9.1+cpu torchaudio==0.8.1+cpu \\
      -f https://download.pytorch.org/whl/torch_stable.html

is valid only for CPython 3.6-3.9. It stays commented.

This script does not install torch. It does not vendor the Ascend port-a3
plugin. That plugin's reference baseline is A3-CANN via aclnn, not CPU PyTorch.
"""

from __future__ import annotations

import sys

COMMENTED_CPU_LINE = (
    "pip install torch==1.8.1+cpu torchvision==0.9.1+cpu "
    "torchaudio==0.8.1+cpu -f https://download.pytorch.org/whl/torch_stable.html"
)
WHEEL_MIN = (3, 6)
WHEEL_MAX = (3, 9)


def wheel_matches(version: tuple[int, int] = sys.version_info[:2]) -> bool:
    return WHEEL_MIN <= version <= WHEEL_MAX


def decision(version: tuple[int, int] = sys.version_info[:2]) -> dict[str, str]:
    ok = wheel_matches(version)
    return {
        "python": ".".join(str(n) for n in version),
        "commented_line": COMMENTED_CPU_LINE,
        "uncomment": "no" if not ok else "only if this interpreter is the install target",
        "reason": (
            "1.8.1+cpu wheel matches this interpreter"
            if ok
            else "1.8.1+cpu wheel does not match this interpreter; leave the line commented"
        ),
        "ascend_reference": "aclnn on A3-CANN, not CPU PyTorch",
        "install_performed": "false",
    }


def main() -> int:
    import json

    print(json.dumps(decision(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
