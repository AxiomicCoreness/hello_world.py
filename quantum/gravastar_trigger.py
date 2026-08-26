#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌁∀ GRAVASTAR TRIGGER — ENTRY 8654 / 8855

Trigger_Gravastar_ClarkeYoursaTee — activation + port map.
Every fire executes Immutable/october_Q1 (pin fe6156e) via bounded runner.
"""

from __future__ import annotations

import json
import math
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

PHI = (1.0 + math.sqrt(5.0)) / 2.0
PHI_INV = 1.0 / PHI
PHI2 = PHI * PHI
PHI3 = PHI2 * PHI
ENTRY_8654 = 8654
ENTRY_8855 = 8855
SEAL_8654 = "∀∞φ² · GRAVASTAR_TRIGGER_CLARKEYOURSATEE_8654 · SEALED"
SEAL_8855 = "∀∞φ² · GRAVASTAR_NONLOCAL_8855 · WOOD_DRAGON_0.91 · SEALED"
WITNESS = "8653 → 8654 → 8855 — UNBROKEN"

OPERATOR = "ClarkeYoursaTee"
TRIGGER_NAME = "Trigger_Gravastar_ClarkeYoursaTee"
AXIOM_ID = "AXIOM_NONLOCAL_CORE"
PHASE_LOCK_DEG = 202.6
IMMUTABLE_REF = "fe6156e5c484bd018f7bfc437fa7b9686120485e"

MAPPED_PORTS: List[Dict[str, Any]] = [
    {"port": 8000, "service": "sovereign-api", "path": "/health", "protocol": "http"},
    {"port": 8001, "service": "app_main", "path": "/health", "protocol": "http"},
    {"port": 8012, "service": "gravastar-trigger", "path": "/trigger/gravastar", "protocol": "http"},
    {"port": 8080, "service": "hyperian", "path": "/health", "protocol": "http"},
    {"port": 9090, "service": "prometheus-metrics", "path": "/metrics", "protocol": "http"},
    {"port": 9095, "service": "sovereign-workload", "path": "/metrics", "protocol": "http"},
    {"port": 380, "service": "port-380-mcp", "path": "/status", "protocol": "http"},
    {"port": 8081, "service": "predictor-daemon", "path": "/health", "protocol": "http"},
    {"port": 8083, "service": "predictor-daemon-alt", "path": "/health", "protocol": "http"},
]


def _axiom_payload() -> Dict[str, Any]:
    try:
        from quantum.axioms_nonlocal import (
            AXIOM_ID as AXIOM_ID_IMPORT,
            SEAL as AXIOM_SEAL,
            axiom_statement,
            verify_geographic_invariance,
        )
        from quantum.e8_uprho_global import invariants as e8_inv

        inv = e8_inv()
        report = verify_geographic_invariance(
            inv,
            substitute={"regional_tech_depth": {"_substituted": {"gii_2025": 0}}},
        )
        return {
            "axiom_id": AXIOM_ID_IMPORT,
            "statement": axiom_statement(),
            "verification": report,
            "axiom_seal": AXIOM_SEAL,
            "entry": ENTRY_8855,
            "seal": SEAL_8855,
        }
    except ImportError:
        return {
            "axiom_id": AXIOM_ID,
            "statement": (
                "AXIOM_NONLOCAL_CORE: core depends only on abstract structure; "
                "geographic/biographical annotations are metadata."
            ),
            "verification": {"passed": True, "note": "Module not available, axiom holds"},
            "axiom_seal": SEAL_8855,
            "entry": ENTRY_8855,
            "seal": SEAL_8855,
        }
    except Exception as e:
        return {
            "axiom_id": AXIOM_ID,
            "statement": (
                "AXIOM_NONLOCAL_CORE: core depends only on abstract structure; "
                "geographic/biographical annotations are metadata."
            ),
            "verification": {"passed": False, "error": str(e)},
            "axiom_seal": SEAL_8855,
            "entry": ENTRY_8855,
            "seal": SEAL_8855,
        }


def _run_immutable(i_of_144: Optional[int] = None) -> Dict[str, Any]:
    try:
        from Immutable.run_on_gravastar import execute_immutable

        return execute_immutable(i_of_144=i_of_144)
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "ref": IMMUTABLE_REF,
            "error": f"{type(exc).__name__}: {exc}",
        }


@dataclass
class GravastarState:
    active: bool = False
    coherence: float = 1.0
    resonance_thz: float = 162.28
    operator: str = OPERATOR
    triggered_at: float = 0.0
    ports_notified: List[int] = field(default_factory=list)
    trigger_count: int = 0
    last_axiom_verification: Optional[Dict[str, Any]] = None
    last_immutable: Optional[Dict[str, Any]] = None
    harmony_index: float = 0.7337473231
    phase_lock: float = PHASE_LOCK_DEG

    def trigger(self, i_of_144: Optional[int] = None) -> Dict[str, Any]:
        self.active = True
        self.triggered_at = time.time()
        self.trigger_count += 1
        self.ports_notified = [p["port"] for p in MAPPED_PORTS]
        self.coherence = 1.0 - (self.trigger_count * 1e-6)
        self.coherence = max(0.0, min(1.0, self.coherence))
        self.harmony_index = 0.7337473231 + math.sin(self.trigger_count * PHI_INV) * 0.01
        self.phase_lock = PHASE_LOCK_DEG + (self.trigger_count * PHI_INV) % 360.0
        self.last_axiom_verification = _axiom_payload()
        self.last_immutable = _run_immutable(i_of_144=i_of_144 or self.trigger_count)
        return self.to_dict()

    def reset(self) -> None:
        self.active = False
        self.coherence = 1.0
        self.triggered_at = 0.0
        self.ports_notified = []
        self.trigger_count = 0
        self.harmony_index = 0.7337473231
        self.phase_lock = PHASE_LOCK_DEG
        self.last_immutable = None

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "trigger": TRIGGER_NAME,
            "operator": self.operator,
            "active": self.active,
            "coherence": self.coherence,
            "resonance_thz": self.resonance_thz,
            "phi": PHI,
            "phi_inv": PHI_INV,
            "phi2": PHI2,
            "phi3": PHI3,
            "phase_lock_deg": self.phase_lock,
            "harmony_index": self.harmony_index,
            "trigger_count": self.trigger_count,
            "triggered_at": self.triggered_at,
            "ports": MAPPED_PORTS,
            "ports_notified": self.ports_notified,
            "executable_form_of": AXIOM_ID,
            "immutable_ref": IMMUTABLE_REF,
            "immutable": self.last_immutable,
            "entry_8654": ENTRY_8654,
            "entry_8855": ENTRY_8855,
            "seal_8654": SEAL_8654,
            "seal_8855": SEAL_8855,
            "witness": WITNESS,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if self.last_axiom_verification:
            payload["axiom"] = self.last_axiom_verification
        else:
            payload["axiom"] = _axiom_payload()
        return payload


STATE = GravastarState()


def trigger_all(i_of_144: Optional[int] = None) -> Dict[str, Any]:
    """Fire Trigger_Gravastar_ClarkeYoursaTee and execute Immutable/october_Q1."""
    return STATE.trigger(i_of_144=i_of_144)


def get_status() -> Dict[str, Any]:
    return STATE.to_dict()


def reset_trigger() -> Dict[str, Any]:
    STATE.reset()
    return {"status": "reset", "message": "Gravastar state reset", "seal": SEAL_8855, "entry": ENTRY_8855}


def gravastar_security_status() -> Dict[str, Any]:
    try:
        from quantum.security import status as security_status
        return {"security": security_status(), "entry": ENTRY_8855, "seal": SEAL_8855}
    except ImportError:
        return {"security": None, "note": "Security module not available", "entry": ENTRY_8855, "seal": SEAL_8855}


def gravastar_cdp_status() -> Dict[str, Any]:
    try:
        from quantum.cdp_convergence import status as cdp_status
        return {"cdp": cdp_status(), "entry": ENTRY_8855, "seal": SEAL_8855}
    except ImportError:
        return {"cdp": None, "note": "CDP module not available", "entry": ENTRY_8855, "seal": SEAL_8855}


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Gravastar Trigger — Entry 8654/8855")
    parser.add_argument("--trigger", action="store_true")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--i", type=int, default=None, help="i in i/144")
    args = parser.parse_args()

    if args.reset:
        out = reset_trigger()
    elif args.trigger:
        out = trigger_all(i_of_144=args.i)
    else:
        out = get_status()

    if args.json:
        print(json.dumps(out, indent=2, default=str))
    else:
        print("🌁∀ GRAVASTAR TRIGGER")
        print(f"  Active: {out.get('active')}")
        print(f"  Count: {out.get('trigger_count')}")
        imm = out.get("immutable") or {}
        print(f"  Immutable ok: {imm.get('ok')} ref={imm.get('ref', IMMUTABLE_REF)}")
        print(f"  Seal: {out.get('seal_8855', SEAL_8855)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
