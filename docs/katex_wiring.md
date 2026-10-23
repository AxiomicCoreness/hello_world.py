# 📝∀ KaTeX wiring — walkthrough ∀📝

## The chain

KaTeXMacros.KATEX_MACROS (Java source, single source of truth)
│
├──► docs/katex_macros.yaml (generated — human-readable)
├──► docs/katex_macros.tex (generated — LaTeX mirror)
│
▼ (pom.xml <testResources> puts docs/katex_macros.yaml and
│  docs/katex_macros.tex on the test classpath; no src/main/resources copy)
KaTeXMacroSetTest.java (reads the classpath copies)

## Why three copies

- **Java source** — the type-safe origin. Changing a macro means
  changing one file. `KaTeXMacros.KATEX_MACROS` is a
  `Map<String, Object>` where each value is either a `String`
  (no arguments) or a `[String, int]` pair (template + arity).
- **YAML in docs/** — for humans. A reader opens one file and sees
  all 31 macros without reading Java.
- **TeX in docs/** — for the LaTeX side. Same macros, `\newcommand`
  form. Drop into a `.tex` document with
  `\input{docs/katex_macros.tex}`.
- **Test classpath** — Maven copies the docs/ YAML and TeX into
  target/test-classes, so the test can assert both declare exactly
  the Java map's keys. Byte-for-byte identity of bodies is not
  asserted; count and key sets are.

## Regenerating

When `KATEX_MACROS` changes, regenerate the derived files:

```bash
# 1. Edit src/main/java/com/fruitfly/brain/KaTeXMacros.java
# 2. Copy the katex.macros block into docs/katex_macros.yaml
# 3. Copy the \newcommand block into docs/katex_macros.tex
```

Until a generator exists, the Java map, YAML and TeX must be kept in
sync by hand. The test catches drift by counting macro declarations,
comparing the YAML and TeX key sets with the Java map, and checking
for specific keys.

## The six keys the test asserts

\half \ket \bra \Tr \Disc \vertex

If any of these is missing from the classpath YAML, the test fails.

## What the test does NOT assert

- That the YAML and the Java map are byte-identical.
- That every LaTeX command in a macro is KaTeX-supported.
- That the TeX mirror bodies match the YAML bodies (only the key sets
  are compared).
- That a renderer successfully renders any macro.

Those are separate concerns. The test guards against accidental
removal of the six core macros and against the YAML file going
missing from the classpath.

## Stokes Mandala micro set (ledger.v2/9300)

Unique micro macros (not a regenerate of the 31-macro dump):

| Path | Role |
|------|------|
| `docs/katex_stokes_mandala_9300_micro.tex` | KaTeX/LaTeX `
ewcommand` micro set |
| `docs/katex_stokes_mandala_9300_micro.yaml` | Human-readable twin |
| `docs/stokes_mandala_9300_fancybox.txt` | ASCII mandala seal (docs asset) |

Core macros: `\stokesflux`, `\Astress` → `\mathcal{A}_{st}`, `\phiflux` → `\varphi^{-1078}`,
`\stokesoint` / `\stokesiint` / `\stokesclassical`.

Seal lock: `ba33cc9b7c4ddac055355aa5ef3b6f7ac9ac25a73e411224ef77055d39ec2667`.
Does **not** alter `KaTeXMacros.KATEX_MACROS` key set (dual-gate / `KaTeXMacroSetTest` unchanged).

