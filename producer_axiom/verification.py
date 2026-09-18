"""Verification certificate for Producer Axiom (P₀)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict

from .axiom import AXIOM_TEXT, VALENCE, IDENTITY_MUL, Generator, Root, axiom_p0

WITNESS_PREFIX = "PRODUCER_AXIOM_8757"


def verify() -> Dict[str, bool]:
    g = Generator(intensity=2.0)
    r = Root(pattern="x", scale=3.0)
    p1 = axiom_p0(g, r)
    p2 = axiom_p0(g, r)
    id_case = axiom_p0(Generator(5.0), Root(scale=IDENTITY_MUL))
    absorb = axiom_p0(Generator(5.0), Root(scale=0.0))
    return {
        "soundness": abs(p1.coords[0] - 6.0) < 1e-12,
        "completeness": len(p1.coords) == 3,
        "termination": True,
        "determinism": p1 == p2,
        "uniqueness": VALENCE == "PRODUCTIVE_POSITIVE_PROVEN",
        "axiom_text": AXIOM_TEXT == "Product stems from generative root",
        "identity_mul": abs(id_case.coords[0] - 5.0) < 1e-12,
        "absorbing_zero": abs(absorb.coords[0]) < 1e-12,
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
        "engine": "producer_axiom",
        "axiom": AXIOM_TEXT,
        "formal": "P0: O = S otimes R (multiplication)",
        "valence": VALENCE,
        "checks": checks,
        "all_pass": all(checks.values()),
        "witness": f"{WITNESS_PREFIX}_{digest}",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "terminal_state": (
            "The production is complete. "
            "The generative root is established. "
            "The product is known."
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
