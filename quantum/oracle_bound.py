"""Solar system is the oracle domain.

Observation surface is /oracle. Extra-solar harmonic probes are out of domain.
No daemon. Workload 0. Device Genesis remains local.
"""
from __future__ import annotations

ORACLE_DOMAIN = "solar_system"
ORACLE_ROUTE = "GET /oracle"
EARTH_ROUTE = "GET /earth"
LATTICE_ROUTE = "GET /lattice"
EXTRA_SOLAR_PROBE = False
GLIESE_581G_IN_DOMAIN = False
DEVICE_GENESIS = False


def oracle_scope() -> dict:
    return {
        "domain": ORACLE_DOMAIN,
        "routes": [ORACLE_ROUTE, EARTH_ROUTE, LATTICE_ROUTE],
        "extra_solar_probe": EXTRA_SOLAR_PROBE,
        "gliese_581g": GLIESE_581G_IN_DOMAIN,
        "device_genesis": DEVICE_GENESIS,
        "posture": "observe_hold",
    }
