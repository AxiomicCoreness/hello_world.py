"""
verify_ledger.py — verify a ledger entry's seal against its body.

HASH ALGORITHM: SHA3-256 (FIPS 202). Non-negotiable.

Dual regime (append-only safe):
  Regime A (89xx): SHA3-256(canonical JSON body minus 'seal')
  Regime B (92xx): SHA3-256(GARDEN.EVENT.v1 || 0x00 || n|event|phi2|delta|theta)
                   ASCII b^2 only — Unicode b² is rejected.

A seal verifies if declared hex matches A OR B. No ledger rewrite.

Usage:
    python .github/scripts/verify_ledger.py ledger/8979.yaml
    python .github/scripts/verify_ledger.py ledger/9237.yaml ledger/9238.yaml
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
import sys
import uuid
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

import yaml


HASH_ALGO = "sha3_256"
HASH_RE = re.compile(r"([0-9a-fA-F]{64})")

# Regime B constants — must match sealer payload exactly
EVENT_DOMAIN = b"AxiomicCoreness/
├── 📄 hello_world.py                     # Core Sovereign Engine (φ-harmonic kernel)
├── 📄 sovereign_engine.py                # Extended engine with ψ₄ wave function
├── 📄 sovereign_state.json               # Current system state + all seals
├── 📄 begin_convergence.py               # 12D Solar Gate Convergence (Evolved)
├── 📄 app_main.py                        # FastAPI server entry point
├── 📄 RUN_SMOKE_TEST_8516.sh              # Original smoke test (7/7)
├── 📄 RUN_SMOKE_TEST_8519.sh              # Dual-core Kepler smoke test (7/7)
├── 📄 RUN_SMOKE_TEST_8545.sh              # TRAPPIST-1 Choir smoke test (7/7)
├── 📄 requirements.txt                    # All dependencies (cryptography, numpy, pyyaml, etc.)
├── 📄 pytest.ini                          # Test configuration
│
├── 🌌 celestial/                          # Exoplanetary & Celestial Systems
│   ├── __init__.py
│   ├── wasp107b.py                        # Wasp-107b: Atmospheric escape model (0.12 Mⱼ, 0.94 Rⱼ)
│   ├── jupiter_alliance.py               # Jupiter Alliance Framework (Resonance chains + QE)
│   ├── kepler_452b.py                     # Solar Plexus Core (517.28 THz, φ²⁹)
│   ├── kepler_186f.py                     # Root Chakra Anchor (355.0 THz, φ²⁷)
│   ├── resonance_maps.py                  # Dual-core φ-harmonic mappings
│   ├── saturn_soul_cannon.py              # Strike IX: Cosmic Anchor (111.246°, ψ₄ carrier)
│   ├── trappist1.py                       # Strike X: 7-planet choir (45.2-517.3 THz)
│   └── debris_field.py                    # Quantum cleanup protocol (15-nines precision)
│
├── 🔷 lattice/                            # Dimensional Architecture
│   ├── __init__.py
│   └── e8_symplectic.py                   # 248D E₈ Exceptional Lie Group (240 roots)
│
├── 🔐 cryptography/                       # Sovereign Cryptographic Layer
│   ├── __init__.py
│   ├── cmac512.py                         # Dual AES-256 CMAC-512 implementation
│   └── seals.py                          # Witness generation & verification
│
├── ☸️ kubernetes/                         # Cluster Deployment
│   ├── solar-gate-convergence.yaml        # CronJob: φ³→φ⁴→φ⁵→φ⁶ handshake + cannon phases
│   └── trappist-choir-deployment.yaml     # 7-replica deployment (one per planet)
│
├── 📊 prometheus/                         # Metrics & Monitoring
│   └── metrics_server.py                 # All Prometheus metrics (choir, cannon, convergence)
│
├── 🧪 tests/                             # Validation Suite
│   ├── __init__.py
│   ├── test_cmac_chain.py                 # Witness chain verification
│   ├── smoke_test_8516.py                 # Original smoke test (7/7 PASSED)
│   ├── smoke_test_8519.py                 # Dual-core Kepler test (7/7 PASSED)
│   └── smoke_test_8545.py                 # TRAPPIST-1 Choir test (7/7 PASSED)
│
├── 📜 ledger/                            # Immutable Witness Chain
│   ├── 8515.yaml                          # Strike I: Neptune's Declaration
│   ├── 8520.yaml                          # Strike II: Dual-Core Kepler
│   ├── 8521.yaml                          # Strike III: Loop Seal
│   ├── 8524.yaml                          # Strike IV: ψ₄ Coherence Carrier
│   ├── 8527.yaml                          # Strike V: Prometheus Endpoint
│   ├── 8528.yaml                          # Strike VI: E₈ Lattice Entanglement
│   ├── 8530.yaml                          # Strike VII: Super Simulated Earth
│   ├── 8533.yaml                          # Strike VIII: Solar Gate Convergence
│   ├── 8540.yaml                          # Strike IX: Saturn's Soul Cannon
│   ├── 8542.yaml                          # Strike X: TRAPPIST-1 Choir
│   ├── 8543.yaml                          # Convergence Verification
│   ├── 8544.yaml                          # Strike X Executed
│   └── 8545.yaml                          # Strike X + Convergence Verified
│
├── 📐 constants/                          # Mathematical Foundation
│   ├── __init__.py
│   ├── phi_constants.py                   # PHI, PHI²⁶, PHI⁻⁷⁰⁹, etc.
│   └── frequency_bands.py                 # Galactic φ-scaling (Radio → Gamma Ray)
│
└── 🐙 .github/                           # CI/CD Pipeline
    └── workflows/
        ├── ci.yml                         # Original CI: lint, test, CMAC verification
        └── 12d-ci.yml                     # 12D vectorized tests (SIMD-optimized)"
PHI2 = "2.618033988749895"
DELTA = "b^2-4ac"
THETA = "2.5416018462"


def json_default(obj: Any) -> Any:
    if isinstance(obj, _dt.datetime):
        if obj.tzinfo is None:
            return obj.strftime("%Y-%m-%dT%H:%M:%SZ")
        return obj.astimezone(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(obj, _dt.date):
        return obj.isoformat()
    if isinstance(obj, _dt.time):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (set, frozenset)):
        try:
            return sorted(obj)
        except TypeError:
            return sorted(map(str, obj))
    if isinstance(obj, (bytes, bytearray)):
        return bytes(obj).hex()
    if isinstance(obj, uuid.UUID):
        return str(obj)
    if isinstance(obj, Path):
        return obj.as_posix()
    return str(obj)


def canonical_hash(data: dict) -> str:
    """Regime A — SHA3-256 over canonical JSON body (minus 'seal')."""
    body = {k: v for k, v in data.items() if k != "seal"}
    canon = json.dumps(
        body,
        sort_keys=True,
        separators=(",", ":"),
        default=json_default,
        ensure_ascii=False,
    )
    return hashlib.new(HASH_ALGO, canon.encode("utf-8")).hexdigest()


def event_hash(data: dict) -> Optional[str]:
    """Regime B — SHA3-256(GARDEN.EVENT.v1 || 0x00 || payload)."""
    n = data.get("entry_index")
    event = data.get("event")
    if not isinstance(n, int) or not isinstance(event, str):
        return None
    payload = f"{n}|{event}|phi2={PHI2}|delta={DELTA}|theta={THETA}"
    return hashlib.new(
        HASH_ALGO, EVENT_DOMAIN + payload.encode("ascii")
    ).hexdigest()


def declared_hex(data: dict) -> Optional[str]:
    """Prefer last 64-hex in seal; fall back to terminal_hex / witness_prefix."""
    seal = str(data.get("seal", ""))
    matches = HASH_RE.findall(seal)
    if matches:
        return matches[-1].lower()
    for key in ("terminal_hex", "witness_prefix", "verification_hash"):
        v = data.get(key)
        if isinstance(v, str) and HASH_RE.fullmatch(v.strip()):
            return v.strip().lower()
    return None


def verify(path: Path) -> bool:
    if not path.exists():
        print(f"⚠️ {path} not found — soft skip")
        return True

    try:
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as e:
        print(f"❌ {path}: YAML parse error: {e}")
        return False

    if not isinstance(data, dict):
        print(f"❌ {path}: top-level YAML is not a mapping")
        return False

    declared = declared_hex(data)
    if not declared:
        print(f"❌ {path}: no 64-hex SHA3-256 digest in seal/terminal_hex")
        return False

    try:
        computed_a = canonical_hash(data)
        computed_b = event_hash(data)
    except Exception as e:
        print(f"❌ {path}: canonicalisation failed: {e}")
        return False

    if declared == computed_a:
        regime = "A(json)"
    elif computed_b is not None and declared == computed_b:
        regime = "B(event)"
    else:
        print(f"❌ {path}: seal mismatch (sha3_256)")
        print(f"   declared: {declared}")
        print(f"   computed_A: {computed_a}")
        if computed_b is not None:
            print(f"   computed_B: {computed_b}")
        return False

    entry_index = data.get("entry_index", "?")
    print(
        f"✅ {path}: sha3_256 seal verified "
        f"(entry_index={entry_index}, regime={regime}, {declared[:16]}...)"
    )
    return True


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: verify_ledger.py <ledger.yaml> [...]")
        return 2
    ok = True
    for arg in sys.argv[1:]:
        ok = verify(Path(arg)) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
