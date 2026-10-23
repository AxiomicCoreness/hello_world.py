# Changelog

## [1.1.0] - 2026-10-23
### Added
- Sparse in-repo vendor of DeepInfer `v4_modules` at
  `deepinfer/model_executor/models/v4_modules/` copied verbatim from
  `deepseek-ai/DeepInfer@9bd9cf243fc53ef9afbf8f04d391d989117d6ab9`
  (24 `.py` files + minimal parent `__init__.py` stubs + `PROVENANCE.md`).
- Skill docs (`SKILL.md`, `assets/context.json`) anchor to that path; note
  post-init mirror under `vendor/DeepInfer/...`. Planck/Xcode remains sovereign;
  v4_modules is model-executor provenance only (not Swift). Bot skill stays
  separate.

## [1.0.0] - 2026-10-23
### Added
- `SKILL.md` with frontmatter (name `xcode-planck-engine`, tagged description
  `xcode-planck-engine-400800db`, tags) and sections Context, Measured run() vs paste,
  XCODE INTEGRATION NOTES (quoted from main), Steps, Known limits, and Verify.
  Measured against main at `bae409d0` where `sovereign/PlanckEngine.swift` gained
  the Xcode header (comments only; math unchanged).
- `assets/context.json` with Swift/Python paths, iOS 16+ target, Port-380
  `syncWithGate` stub, graphviz/seaborn Python-only constraint, header presence,
  and **measured** `PlanckEngine.run()` values (paste deltas recorded).
- `xcode_planck_scripts/check_xcode.py`: validates XCODE header, no graphviz in
  Swift, φ parity, companion SwiftUI files, and measured run() anchors. Package
  named `xcode_planck_scripts` (not `scripts`) so skill-root `sys.path` cannot
  shadow the repo `scripts/` package.
- `evals/conftest.py` and `evals/test_xcode_planck.py` (header, syncWithGate,
  φ agreement, no graphviz import, SI constants, requirements pins, measured
  run() anchors, package name).

### Notes
- Paste `hawkingTempK≈1.25e-19` does **not** match code output
  (`8.405783e+07`); evals use measured.
