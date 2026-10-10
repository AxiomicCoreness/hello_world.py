# 📝∀ KaTeX wiring — walkthrough ∀📝

## The chain

KaTeXMacros.KATEX_MACROS (Java source, single source of truth)
│
├──► docs/katex_macros.yaml (generated — human-readable)
├──► docs/katex_macros.tex (generated — LaTeX mirror)
└──► src/main/resources/katex_macros.yaml (classpath copy)
│
▼
KaTeXMacroSetTest.java (reads classpath copy)

## Why three copies

- **Java source** — the type-safe origin. Changing a macro means
  changing one file. `KaTeXMacros.KATEX_MACROS` is a
  `Map<String, Object>` where each value is either a `String`
  (no arguments) or a `[String, int]` pair (template + arity).
- **YAML in docs/** — for humans. A reader opens one file and sees
  all 30 macros without reading Java.
- **TeX in docs/** — for the LaTeX side. Same macros, `\newcommand`
  form. Drop into a `.tex` document with
  `\input{docs/katex_macros.tex}`.
- **YAML on the classpath** — so the test can assert the YAML matches
  the Java map. Byte-for-byte identity is not asserted; count and key
  presence are.

## Regenerating

When `KATEX_MACROS` changes, regenerate the derived files:

```bash
# 1. Edit src/main/java/com/fruitfly/brain/KaTeXMacros.java
# 2. Copy the katex.macros block into docs/katex_macros.yaml
# 3. Copy the \newcommand block into docs/katex_macros.tex
# 4. Copy docs/katex_macros.yaml to src/main/resources/
```

Until a generator exists, the three copies must be kept in sync by
hand. The test catches drift by counting macro declarations and
checking for six specific keys.

## The six keys the test asserts

\half \ket \bra \Tr \Disc \vertex

If any of these is missing from the classpath YAML, the test fails.

## What the test does NOT assert

- That the YAML and the Java map are byte-identical.
- That every LaTeX command in a macro is KaTeX-supported.
- That the TeX mirror matches the YAML.
- That a renderer successfully renders any macro.

Those are separate concerns. The test guards against accidental
removal of the six core macros and against the YAML file going
missing from the classpath.