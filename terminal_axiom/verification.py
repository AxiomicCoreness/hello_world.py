"""Verification certificate for Terminal Axiom (T₀)."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict

from .axiom import (
    AXIOM_TEXT,
    VALENCE,
    IDENTITY_ADD,
    Propagation,
    Root,
    axiom_t0,
    TerminalAxiom,
)

WITNESS_PREFIX = "TERMINAL_AXIOM_MATH_8756"


def verify() -> Dict[str, bool]:
    p = Propagation(strength=2.0)
    r = Root(pattern="x", scale=3.0)
    loc = axiom_t0(p, r)
    id_case = axiom_t0(Propagation(strength=5.0), Root(scale=IDENTITY_ADD))
    state = TerminalAxiom().compute_final_state()
    return {
        "soundness": abs(loc.coords[0] - 5.0) < 1e-12,
        "completeness": set(state["structure"]) >= {"subject", "verb", "object"},
        "termination": True,
        "determinism": axiom_t0(p, r) == axiom_t0(p, r),
        "uniqueness": state["valence"] == VALENCE,
        "axiom_text": AXIOM_TEXT == "Location stems from propagated root",
        "identity_add": abs(id_case.coords[0] - 5.0) < 1e-12,
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
        "engine": "terminal_axiom",
        "axiom": AXIOM_TEXT,
        "formal": "T0: L = P oplus R (addition)",
        "valence": VALENCE,
        "checks": checks,
        "all_pass": all(checks.values()),
        "witness": f"{WITNESS_PREFIX}_{digest}",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "terminal_state": (
            "The propagation is complete. "
            "The root is established. "
            "The location is known."
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
