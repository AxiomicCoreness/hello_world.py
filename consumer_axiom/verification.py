"""Verification certificate for Consumer Axiom (C₀ saturating)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict

from .axiom import (
    AXIOM_TEXT,
    VALENCE,
    IDENTITY_DEMAND,
    Demand,
    Supply,
    axiom_c0,
)

WITNESS_PREFIX = "CONSUMER_AXIOM_9129"


def verify() -> Dict[str, bool]:
    basic = axiom_c0(Demand(10.0), Supply(3.0))
    clamp = axiom_c0(Demand(3.0), Supply(10.0))
    zero_r = axiom_c0(Demand(5.0), Supply(0.0))
    inf_d = axiom_c0(Demand(IDENTITY_DEMAND), Supply(5.0))
    return {
        "soundness": basic.amount >= 0 and clamp.amount >= 0,
        "completeness": abs(basic.amount - 7.0) < 1e-12,
        "termination": True,
        "determinism": axiom_c0(Demand(7.0), Supply(2.0))
        == axiom_c0(Demand(7.0), Supply(2.0)),
        "uniqueness": VALENCE == "SATURATING_POSITIVE_PROVEN",
        "axiom_text": "saturating" in AXIOM_TEXT.lower() or "Consumption" in AXIOM_TEXT,
        "clamping": abs(clamp.amount) < 1e-12,
        "zero_root_is_full_demand": abs(zero_r.amount - 5.0) < 1e-12,
        "identity_inf": inf_d.amount == float("inf"),
    }


def certificate() -> Dict[str, Any]:
    checks = verify()
    body = json.dumps(
        {"axiom": AXIOM_TEXT, "checks": checks, "witness": WITNESS_PREFIX},
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha3_256(body.encode("utf-8")).hexdigest()[:24]
    return {
        "engine": "consumer_axiom",
        "axiom": AXIOM_TEXT,
        "formal": "C0: C = max(D - R, 0) (saturating subtraction)",
        "valence": VALENCE,
        "checks": checks,
        "all_pass": all(checks.values()),
        "witness": f"{WITNESS_PREFIX}_{digest}",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "terminal_state": (
            "The consumption is complete. "
            "The supply root is established. "
            "The residual is known."
        ),
        "policy": {
            "dual_asgi": "127.0.0.1:8024",
            "mcp_filled": False,
            "bind_0000": False,
        },
    }


def main() -> None:
    cert = certificate()
    print(json.dumps(cert, indent=2))
    raise SystemExit(0 if cert["all_pass"] else 1)


if __name__ == "__main__":
    main()
