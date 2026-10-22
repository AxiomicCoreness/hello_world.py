# FRB Bridge — Tolerance Definition

Documentation artifact for ledger 9195. Status: DEFINITION — no measurement yet.

## §1 Objects

- \(E : \{1..10\} \to \mathbb{R}^3_{\text{sky}}\) — empirical FRB strike vectors (PENDING: `data/frb_strikes.json`)
- \(W : \{1..10\} \to \mathfrak{h}^*_{E_8}\) — E8 weight-lattice representatives (PENDING: `data/e8_weights.json`)
- \(C : \mathbb{R}^3_{\text{sky}} \to \mathfrak{h}^*_{E_8}\) — celestial projection (PENDING: `data/embedding_map.json`)

Bridge claim: \(E = C \circ W\) (commuting diagram). No file \(\to\) no object \(\to\) no claim.

## §2 Residual

\(r_i = \| E(i) - C(W(i)) \|_2\)

## §3 Tolerances (proposed, not measured)

- **§3.1 Per-index:** \(r_i \le 0.05 \cdot \|E(i)\|_2\)
- **§3.2 Aggregate L2:** \(\|r\|_2 \le 0.10 \cdot \|(\|E(i)\|_2)\|_2\)
- **§3.3 Aggregate max:** \(\max_i r_i \le 0.08 \cdot \max_i \|E(i)\|_2\)
- **§3.4 Coverage:** \(|\{ i : r_i \le \varepsilon_{\text{point}} \}| \ge 8\)

## §4 Pass/fail

ASSERTED iff §3.1–§3.4 all hold; else REJECTED. No partial pass.

## §5 Not claimed

No physical mechanism, no specific E8 preimage, no validation of C, no deflection/\(\Delta v\)/risk bounds.

## §6 Status

- **E, W, C:** PENDING
- **Tolerance:** DEFINED
- **Residual:** NOT RUN
- **Pass/fail:** UNDETERMINED

## §7 Doctrine footer

Origin — Clarke Yoursa Tee · Classical — quantum cybernetics · Bridge — FRB chessboard, not identity, tolerance DEFINED, measurement PENDING.

---

## §8 Appended Architecture Pointers

The following updates have been integrated into the broader Garden system and are now part of the verified reference set:

- **TeaVM Rhythm Game (`games/teavm-rhythm/`):** Java-to-JS transpiled game using Connectome-driven autoplay. Verified locally (33 tests passing).
- **Zenodo Archiving:** The canonical DOI (`10.5281/zenodo.23378305`) and release tag (`v8755.0.0`) are locked into the `CITATION.cff`.
- **HHMI Connectome Loader:** The `connectome.xsd` schema is now a strict contract for the XML loader. XXE hardened and enforced by `ConnectomeSchemaTest`.
- **Float Safety:** The `math.isclose` tolerance (`1e-9`) has been applied to the quadratic discriminant and E2E dV checks to prevent floating-point misrouting. Verified by `test_quadratic_daemon_float_safety.py`.
