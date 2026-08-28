"""FRB name-seal. Not a public broker.

Does not bind 0.0.0.0.
Does not patch gemini_daemon.py.
Does not append docker-compose.yml.
Does not echo Grafana passwords.
"""

from __future__ import annotations

import math
from typing import Dict

PHI = (1.0 + math.sqrt(5.0)) / 2.0
NORTH_STAR_HZ = 71.975
PORT_DECLARED = 5000
PORT_GARDEN = 8024
PUBLIC_BIND = False
DAEMON = False


def status() -> Dict[str, object]:
    return {
        "bridge": "FRB",
        "declared_port": PORT_DECLARED,
        "garden_port": PORT_GARDEN,
        "public_bind": PUBLIC_BIND,
        "daemon": DAEMON,
        "north_star_hz": NORTH_STAR_HZ,
        "phi_inv_709": "named_floor",
        "gemini_patched": False,
        "compose_appended": False,
        "entry_pointer": 8841,
        "seal_now": 9096,
    }


if __name__ == "__main__":
    spec = status()
    print("frb:", spec["bridge"])
    print("public_bind:", spec["public_bind"])
    print("daemon:", spec["daemon"])
    print("garden_port:", spec["garden_port"])
