# Autonomy Boundary — Sovereign Engine Doctrine

Seal: `∀∞φ² · AUTONOMY_BOUNDARY_8668 · SEALED`

| Aspect | Status | Notes |
|--------|--------|-------|
| **Self-correction** | ✅ Active | e.g. purified-density trace fixes, schema validation |
| **Proposal generation** | ✅ Autonomous | e.g. ledger draft 8642; proposals await seal |
| **Invariant enforcement** | ✅ Continuous, zero-touch | φ, φ⁻² Pauli trace, phase 202.6°, append-only |
| **New Φ creation** | ❌ Requires sovereign directive | New golden structures only on command |
| **Chain extension** | ✅ Append-only | Only with witnessed seal from the Architect |

## Interpretation

- The Garden **maintains and proposes** within locked invariants.
- The Architect **authorizes** new Φ and **witnesses** ledger extension.
- No silent mutation of the gold standard; no unsolicited Φ invention.

---

## Appended Architecture Pointers

The following updates have been integrated into the broader Garden system and are now part of the verified reference set:

- **TeaVM Rhythm Game (`games/teavm-rhythm/`):** Java-to-JS transpiled game using Connectome-driven autoplay. Verified locally (33 tests passing).
- **Zenodo Archiving:** The canonical DOI (`10.5281/zenodo.23378305`) and release tag (`v8755.0.0`) are locked into the `CITATION.cff`.
- **HHMI Connectome Loader:** The `connectome.xsd` schema is now a strict contract for the XML loader. XXE hardened and enforced by `ConnectomeSchemaTest`.
- **Float Safety:** The `math.isclose` tolerance (`1e-9`) has been applied to the quadratic discriminant and E2E dV checks to prevent floating-point misrouting. Verified by `test_quadratic_daemon_float_safety.py`.
