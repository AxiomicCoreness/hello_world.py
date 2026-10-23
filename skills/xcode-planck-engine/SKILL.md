---
name: xcode-planck-engine
description: "xcode-planck-engine-400800db. Use when building or running the Sovereign PlanckEngine in Apple Xcode / SwiftUI (sovereign/PlanckEngine.swift with ContentView.swift and AxiomicApp.swift); keep Swift/Python phi math in parity with planck_engine_v2.py; graphviz and seaborn are Python-side only (t_rotator / plotting); stdlib stripping is Xcode Release config, never hand-edited into Swift."
tags:
  - xcode-planck-engine-400800db
  - "context:Xcode iOS16+,SwiftUI,PlanckEngine,Port-380 syncWithGate,no graphviz in Swift"
---

# xcode-planck-engine

In-repo skill for wiring **Sovereign PlanckEngine** into Apple **Xcode / SwiftUI**.
Layout mirrors `skills/hhmi` and `skills/bms-display-mock`. Lives at
`skills/xcode-planck-engine/` on `AxiomicCoreness/hello_world.py`. Measured against
main at `bae409d0` (`sovereign: add Xcode integration notes header to PlanckEngine.swift`).

## Context (checked against main)

- Canonical Swift math: `sovereign/PlanckEngine.swift` (includes `XCODE INTEGRATION NOTES`
  header and `syncWithGate(base: URL) async throws` stub).
- Canonical Python twin: `sovereign/planck_engine_v2.py` (`PlanckEngine.run()` → dict).
- UI entry points at repo root: `AxiomicApp.swift` (`@main`), `ContentView.swift`.
- Port-380 bridge stub on Swift: `PlanckEngine.syncWithGate(base: URL) async throws`
  (implementation omitted; updates static φ vars from JSON when the gate is online).
- Offline defaults: static `phi`, `phi_5`, `phi_9`, `phi_inv_709`, `phi_inv_1000`.
- **Graphviz is Python-only.** `requirements.txt` pins `graphviz>=0.20.1` and
  `seaborn>=0.13.0` for `scripts/t_rotator_graphs.py` / plotting. Do **not**
  import or link graphviz from Swift / Xcode.
- **Stdlib stripping** is Xcode Release configuration automatic behavior. Do not
  manually strip `Foundation`; it is required for Math.

## Measured `PlanckEngine.run()` vs paste targets

Paste numbers were checked by executing `sovereign.planck_engine_v2.PlanckEngine.run()`
on main (`bae409d0` tree). **Use measured values in tests.** Notable deltas:

| key | paste | measured | notes |
| --- | --- | --- | --- |
| hawkingTempK | 1.25e-19 | 8.405783e+07 | **paste wrong vs code** (~10^26×); code divides by `rsMeters` not `M` |
| sBellCorrected | 4.576 | 4.57649122254 | paste is 3-dp rounding |
| dSdtOption1 | -1597.0 | -1596.9844719 | paste rounding of -144·φ⁵ |
| dSdtOption2 | -987.0 | -986.99068314 | paste rounding of -144·φ⁴ |
| eps145 | 1.368e-209 | 1.367057195144e-209 | paste ~0.07% high |
| zetaBound | 4.3227 | 4.32076776236 | paste ~0.045% high |

Evals assert measured values (with tight relative tolerances), not the paste.

## XCODE INTEGRATION NOTES (quoted from main)

`sovereign/PlanckEngine.swift` on main already carries this header (commit
`bae409d0`):

```
 * ============================================================================
 * XCODE INTEGRATION NOTES
 * ============================================================================
 * 1. Open Xcode -> File -> New -> Project -> iOS App (SwiftUI).
 * 2. Name the project "AxiomicCoreness" (or similar).
 * 3. Delete the default ContentView.swift and [AppName]App.swift.
 * 4. Drag this file (PlanckEngine.swift), ContentView.swift, and
 *    AxiomicApp.swift into the Xcode project navigator.
 * 5. Ensure "Copy items if needed" is checked.
 * 6. Target iOS 16.0+ (required for standard SwiftUI grid/list features).
 *
 * NOTE ON GRAPHVIZ & STDLIB:
 * - Graphviz is NOT used here. SwiftUI handles rendering natively.
 * - Stdlib stripping is handled by Xcode's release configuration automatically.
 *   Do not manually strip standard libraries; Foundation is required for Math.
 * ============================================================================
```

## Steps

1. Read `assets/context.json` for paths, pins, measured run() values, and constraints.
2. Confirm `sovereign/PlanckEngine.swift` contains `XCODE INTEGRATION NOTES`
   and `syncWithGate`.
3. In Xcode: new iOS App (SwiftUI), target **iOS 16.0+**, drag in
   `PlanckEngine.swift`, `ContentView.swift`, `AxiomicApp.swift` with
   "Copy items if needed".
4. Keep math edits dual-homed: any φ / SI constant change in Swift must land in
   `sovereign/planck_engine_v2.py` (and vice versa). Re-run evals; update
   measured table if outputs change.
5. For visualizations use Python (`scripts/t_rotator_graphs.py`, seaborn,
   graphviz). Never add those deps to the Xcode project.
6. Optional helper: `python3 -P xcode_planck_scripts/check_xcode.py` from this
   folder (exit 0 ok, 1 on missing header / graphviz leak / φ mismatch).

## Known limits

- `syncWithGate` is a stub; Port-380 JSON schema for live φ updates is not
  specified in this skill.
- `ContentView.swift` hard-codes a LAN URL (`http://192.168.1.20:8025`); that is
  a local render client, unrelated to Planck math or graphviz.
- This skill does not ship an `.xcodeproj`; agents must create the Xcode project
  by following the header notes.
- Hawking temperature in code uses `rsMeters` in the denominator (not mass `M`),
  so `hawkingTempK` is ~8.41e7 K rather than the paste's ~1.25e-19 K. Fixing that
  formula is out of scope for this skill; evals lock the current code output.

## Verify

- `python3 -P -m pytest -q evals` from this folder: all tests pass.
- The package is `xcode_planck_scripts`, not `scripts`, so `evals/conftest.py`
  putting the skill root first on `sys.path` cannot shadow the repo's top-level
  `scripts/` package.
