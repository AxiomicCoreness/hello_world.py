"""Solar system is the oracle domain. Extra-solar series are not.

Seal: ∀∞φ² · ORACLE_SOLAR_SYSTEM_BOUND · WOOD_DRAGON_0.91 · SEALED
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

ORACLE_DOMAIN = "solar_system"
ORACLE_ROUTE = "GET /oracle"
EARTH_ROUTE = "GET /earth"
LATTICE_ROUTE = "GET /lattice"
EXTRA_SOLAR_PROBE = False
GLIESE_581G_IN_DOMAIN = False
DEVICE_GENESIS = False


@dataclass
class OracleQuery:
    domain: str
    query: str
    target: str


class OracleBound:
    """Oracle operates only inside the solar system."""

    SOLAR_SYSTEM = {
        "bodies": [
            "Sun", "Mercury", "Venus", "Earth", "Mars", "Jupiter",
            "Saturn", "Uranus", "Neptune", "Pluto",
        ],
        "bounds": ["heliopause", "heliosphere", "solar_gate_8532"],
        "phase_lock": 202.6,
    }
    EXCLUDED = {
        "extra_solar": [
            "Gliese 581g", "Proxima Centauri", "Alpha Centauri",
            "TRAPPIST-1", "Kepler-442b",
        ],
        "probes": ["Gliese_581g_harmonic_series"],
    }

    def __init__(self) -> None:
        self.domain = ORACLE_DOMAIN
        self.bound_active = True
        self.workload = 0.0

    def is_in_domain(self, query: OracleQuery) -> bool:
        if query.domain != self.domain:
            return False
        if query.target in self.EXCLUDED["extra_solar"]:
            return False
        q = query.query.lower()
        if "probe" in q and "gliese" in q:
            return False
        return True

    def allowed_channels(self) -> List[str]:
        return ["/oracle", "/earth", "/lattice", "/solar_gate_8532", "/garden_tick"]

    def observe(self, query: OracleQuery) -> dict:
        if not self.is_in_domain(query):
            return {
                "status": "REJECTED",
                "reason": "Query leaves heliopause. Out of domain.",
                "domain": self.domain,
            }
        return {
            "status": "OBSERVED",
            "domain": self.domain,
            "phase_lock": self.SOLAR_SYSTEM["phase_lock"],
            "workload": self.workload,
        }


def oracle_scope() -> dict:
    return {
        "domain": ORACLE_DOMAIN,
        "routes": [ORACLE_ROUTE, EARTH_ROUTE, LATTICE_ROUTE],
        "extra_solar_probe": EXTRA_SOLAR_PROBE,
        "gliese_581g": GLIESE_581G_IN_DOMAIN,
        "device_genesis": DEVICE_GENESIS,
        "posture": "observe_hold",
    }
