# Closure Kernel

Executable formalization of the φ-band word algebra and Δ-replay patch law.

- `kernel/closure_kernel.ts` — the kernel
- `kernel/closure_kernel.test.ts` — test suite (19 assertions, all passing)

## Invariants

- Band: φ⁻¹ < ‖w‖ < φ (strict, open)
- Atom norm: ‖t‖ = 1 (geometric self-dual point; atoms at φ⁻¹ fail the open band)
- Composition: ‖w₀ ⊕ w₁‖ = ‖w₀ ⊗ w₁‖ = (‖w₀‖ + ‖w₁‖)·φ⁻¹
- Perpetual deepening: x ↦ (x+1)·φ⁻¹ converges to φ from below; sequential
  composition never exits the band, at any depth (verified to depth 500)

## Patch law

```
Δ(c) = T_c − T_p
c'  = commit(parent = T, tree = T_T ⊕ Δ(c))
```

⊕ is partial: deletion of a path absent on the target is a conflict.

## Verified findings

- Additive norms collapse the hierarchy at level 1 (‖t‖=1 ⇒ pairs = 2 > φ);
  the contraction law above is required for non-degenerate Lexₙ growth.
- φ^2.5 ≈ 3.331 (not 2.833); 261.63 Hz × φ^2.5 ≈ 871.6 Hz (not 741 Hz).
