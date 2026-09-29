# Quadratic Discriminant Slot — Catalogue and Lemmas

## Method (six steps that produced the final code)

1. Fix a classical object: the quadratic with coefficients (a, b, c).
2. Parameterize one constant: replace the literal 4 in D = b² − 4ac with a free slot k.
3. Identify invariants by inspection: Re = −b/(2a) is fixed under k (Vieta for the sum of roots).
4. Locate the critical point: solve D(k) = 0 → k_crit = b²/ac.
5. Numerical certification: sweep k, assert to 1e-12, record exit codes. This tests points, not the function.
6. Catalogue the failed attempts and lock the consistent classical version.

Steps 3–5 are engineering hygiene. Steps 1–2 and 6 are version-control discipline. The mathematical content is exhausted by the two lemmas below.

## Attempt history

| # | Convention | Notes | Outcome |
|---|------------|-------|--------|
| 1 | D(k) = k·ac − b² (slot-style) | Lua original | Superseded |
| 2 | Same | Python one-liner (constants only) | Diagnostic |
| 3 | Same | Full Python module + regime self-test | Superseded |
| 4 | Classical D = b² − k·ac | Broken real-part table, wrong Vieta product for complex roots | Rejected |
| 5 | Classical | Correct regimes, incorrect empirical product (a² − b²) | Fixed |
| 6 | Classical D = b² − k·ac | Correct product, real-part invariant, θ only in complex regime | Final |

## Locked constants (Attempt #6)

```
a       ≈ 1.4115016583
b       ≈ 2.6015528764
c       ≈ 2.7182818285
k_crit  ≈ 1.7639628729
Re      ≈ -0.9215550195
```

## Mathematical content

**Lemma 1 (Sum invariance).**  
Let a, b, c ∈ ℝ with a ≠ 0 and let k ∈ ℝ. Define

    p_k(Q) = a Q² + b Q + (k/4) c.

If r₁, r₂ ∈ ℂ are the roots of p_k (counted with multiplicity), then

    (r₁ + r₂)/2 = −b/(2a)

for every k.

*Proof.* By Vieta the sum of the roots is −b/a, independent of the constant term and therefore independent of k. Divide by 2. ∎

**Lemma 2 (Regime classification).**  
Let Δ(k) = b² − k·ac. Assume ac > 0. Then Δ is strictly decreasing, Δ(k_crit) = 0 where k_crit = b²/(ac), and:

- k < k_crit ⟹ two distinct real roots;
- k = k_crit ⟹ one real root of multiplicity two;
- k > k_crit ⟹ complex-conjugate pair with real part −b/(2a).

*Proof.* Δ'(k) = −ac < 0, so Δ is strictly decreasing. Direct substitution gives Δ(k_crit) = 0. The classification is the standard sign analysis of the discriminant. ∎

These two statements exhaust the mathematical content of the construction. Numerical sweeps, exit codes, and regime tables are verification infrastructure, not mathematics.

## Notes on framing

- The window-capacity / Kolmogorov / Markovian material is standard symbolic dynamics and algorithmic information theory. It is independent of the quadratic engine unless a proved correspondence is supplied.
- Language such as “crystallized”, “locked”, “sovereign core”, or “invariant status secured” is decorative. The lemmas above are the content.
- A one-parameter family of polynomials is interesting when the total space is studied (degeneration, monodromy, etc.). Treating each fibre in isolation and reporting its roots is ordinary calculation.
