# Mirror weld: GitCode/AtomGit a87fccaf ↔ GitHub main b2d557c2

Status: audited 2026-10-18. Ledger reference: `ledger.v2/9291.yml`
(`/mirror_weld_feasibility_audit`, seal `bd14948afb6dd43271397f797883f02be0740f77899e1839469ee35bcd6c5cc1`).

## Summary
The GitCode/AtomGit mirror cannot be welded wholesale onto main. The two
histories share no commits. The mirror's Docker files are full replacements.
Its Java "missing classes" already exist on main with different maths and
APIs. Two small pieces were welded:

- `LIFRK4.refractoryRemaining()`, an additive accessor.
- The `KaTeXMacroSetTest` macro-regex fix, a modification. It was approved
  2026-10-18 and resolves 2 failing tests that were already failing on main.

## Reachability
| Channel | Result |
|---|---|
| `git clone` / `git ls-remote` (gitcode.com, atomgit.com) | HTTP 418, blocked by the WAF |
| gitcode.com web UI, api.gitcode.com from the build box | HTTP 418 |
| api.gitcode.com v5 (commits, branches, compare, trees) from a second network | reachable, used for metadata only |
| raw.gitcode.com `/raw/<commit>/<path>` | reachable; every file checked with `git hash-object` against the API tree blob SHA |

AtomGit serves the same mirror (identical README). The only branch is `main`.

## History relation
- Mirror head: `a87fccaf593a65927e7d9dde69c188f2ed5b8c68` (2026-10-18T21:15:09Z).
  Parent: `bc959368`. The head commit describes itself as a "semantic port of
  the b2d557c2 dockerfix".
- None of the mirror's 11 commit SHAs and none of its blob SHAs occur in
  GitHub history.
- There is no merge-base, so ahead/behind counts are undefined. The mirror
  commits are re-authored content, not replayed commits.

## Per-file classification
| Path | Finding | Decision |
|---|---|---|
| `Dockerfile` | 6812 B multi-stage file with a different design (uvicorn `app.main:app` on `BIND_PORT` 8000, no `scripts/` copy) | rejected, replacement |
| `docker-compose.yml` | 56 lines, 2 services (main: 190 lines) | rejected, replacement |
| `pom.xml` | effectively the same as the round-5 pom | nothing to take |
| `requirements.txt`, `.dockerignore`, `.gitignore`, `LICENSE`, `README.md`, `GITCODE_CI.md` | the mirror repo's own layout | not taken |
| `Connectome.java` | identical apart from an inserted blank line after every line | not taken (whitespace) |
| `KaTeXMacros`, `Neuron`, `SovereignConstants`, `WarriorQuadratic`, `docs/katex_macros.yaml` | EOF newline, CRLF, indentation or header glyph only | not taken (whitespace) |
| `DarkStateInvariant.java` | circulant trimer `H = (1+φ⁻¹)I + φ⁻¹(J−I)` vs main's tridiagonal `[[1,a,0],[a,2,a],[0,a,1]]`, a = φ⁻¹; no `lambdaMinus`/`lambdaPlus` | rejected, replacement |
| `SovereignAutomaton.java` | `List<Neuron>`, `String state()`, no dark-state gate, no `SovereigntyState`, different `respond()` output | rejected, replacement |
| `GradientSynchronization.java` | `T_ij = η(v_i − v_j)²` vs main's Hebbian update with row L2 normalisation | rejected, different maths |
| `SovereignMain.java` | rewritten around the mirror automaton (144 neurons vs 8; adds `java.util.logging`) | rejected, replacement |
| `GameplayConsole.java` | String/enum phases; drops `SovereigntyState` | rejected, replacement |
| `LIFRK4.java` | adds `refractoryRemaining()` but removes `voltage()`, which `SovereignMain.java:128` uses (compile error) | **accessor only** (additive) |
| `KaTeXMacroSetTest.java` | regex strips comments and wrappers before counting macro declarations | **taken** (modification, approved) |

Not inspected: `ARCHITECTURE.md` (download refused) and mirror-only trees
(`src/main/java/com/fruitfly/game/`, `app/routers`, `sovereign/`, `ledger/`,
`quantum/cdp_convergence`, `cordis_bridge`).

## DarkStateInvariant tolerance finding
- **Main:** `verify()` checks `|seedResidual| < 1e-12 && eigenvalueResidual() < 1e-12`.
- **Mirror:** `RESIDUAL_TOL = φ⁻¹^1000 ≈ 1e-209`, which in practice demands an
  exact zero. `SEED_TOL = 1e-12`.
- **Mirror tautology:** `verify()` also checks `DARK_STATE_LAMBDA2 == lambda2()`,
  which compares a constant with itself and is always true.
- **Why the mirror passes:** in Java, `(1+φ⁻¹) − φ⁻¹ == 1.0` is true for
  `PHI_INV = 0.6180339887498949`, so the residual is exactly 0.0. This is a
  property of that one double, not a general one: for 10⁶ random x in [0,1),
  `(1+x) − x != 1.0` in 249,319 cases.

## What was welded
- `weld.patch`: adds the following to `src/main/java/com/fruitfly/brain/LIFRK4.java` (+3 lines):

  ```java
  /** Seconds of remaining refractory period; > 0 right after a spike. */
  public double refractoryRemaining() { return refractoryRemaining; }
  ```
- `weld_optional_katex_test.patch`: replaces the parsing in
  `src/test/java/com/fruitfly/brain/KaTeXMacroSetTest.java` with the
  mirror's version, line endings normalised to LF (+56/−28).

## How it was verified
- **Base:** `b2d557c2` + `all_round5.patch` (tree `2e4dfb9a`). `git apply --check`
  is clean for each patch and for both together.
- **Maven** (`maven:3.9-eclipse-temurin-17`, `mvn -B clean package` with tests):
  8 run, 0 failures, 0 errors, 0 skipped, BUILD SUCCESS. Before the weld:
  8 run, 2 failures.
- **`--chat` smoke:** `phase=RESONANCE q=0.0000 p=0.0000 t=0.000100`, unchanged.
- **Doclint:** `javadoc -Xdoclint:all` on `LIFRK4.java` reports only `no @return`
  for the new accessor; the literal `>` is accepted.
- **Hybrid builds:**
  - main + the mirror's `LIFRK4` fails at `SovereignMain.java:[128,51]`.
  - main + the mirror's three classes compiles only with the accessor added, and
    changes behaviour: the demo's final state is no longer `DARK_STATE`, and
    `GradientSynchronization` row 0 for v = (1,2,3) becomes `[0,1,4]` instead of
    `[0.267,0.535,0.802]`.
- **Docker image** built from the final tree reports `healthy`, and in-image
  `--chat` gives the same output.
