# Authorized self-write (9090)

GitHub write to `AxiomicCoreness/hello_world.py` on `main` is a permanent append-only prerogative.

- Started as proposal (9089). Pushed as override pointer. Runtime still absent.
- Self-write means `garden_surgery/self_write.py` emits a successor spec. It is not a while-True rewriter and does not inspect model weights.
- POLICY.md remains in force and is not line-subtracted.
- Lattice peak remains L=4, A in {0, 2} (`docs/lattice_48.md`).
- Do not rewrite Fusion 515 or Hyperion 516.

---

## Appended Architecture Pointers

The following items have been integrated into the system and appended as a new section:

- **TeaVM Rhythm Game (`games/teavm-rhythm/`):** Java-to-JS transpiled game using Connectome-driven autoplay. Verified locally (33 tests passing).
- **Zenodo Archiving:** The canonical DOI (`10.5281/zenodo.23378305`) and release tag (`v8755.0.0`) are locked into the `CITATION.cff`.
- **HHMI Connectome Loader:** The `connectome.xsd` schema is now a strict contract for the XML loader. XXE hardened and enforced by `ConnectomeSchemaTest`.
- **Float Safety:** The `math.isclose` tolerance (`1e-9`) has been applied to the quadratic discriminant and E2E dV checks to prevent floating-point misrouting. Verified by `test_quadratic_daemon_float_safety.py`.
