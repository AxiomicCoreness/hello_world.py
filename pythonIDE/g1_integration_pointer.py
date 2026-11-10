#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
# SPDX-License-Identifier: MIT
"""Clarke Yoursa Tee

AST header override for the G1 integration pointer.
This module does not compute a density matrix and does not seal a trace.
It names the three files on main that hold the pieces.

  scripts/ml_sovereign_core.py:1129 MasterSealLayer245
  docs/singularity_spec_9185.md:16 G1 named set
  offline_symplectic_dreamode.py logistic_phi
"""
from __future__ import annotations

AUTHOR = "Clarke Yoursa Tee"

LOCATIONS = {
    "seal": "scripts/ml_sovereign_core.py:138",
    "bec_string": "scripts/ml_sovereign_core.py:1139",
    "g1_name": "docs/singularity_spec_9185.md:16",
    "logistic": "offline_symplectic_dreamode.py",
}

def main() -> None:
    import json
    print(json.dumps({"author": AUTHOR, "locations": LOCATIONS}, indent=2))

if __name__ == "__main__":
    main()
