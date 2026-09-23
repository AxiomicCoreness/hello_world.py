// ─── exactness.ts — Δ_B ⊣ ⊕_B, with room for paradox ──────────────────────
// THEOREM (typed):
//   Forward  (free):   C(s1) = C(s2)  =>  Δ_B(s1) = Δ_B(s2)
//   Backward (earned): Δ_B(s1) = Δ_B(s2)  =>  C(s1) = C(s2)
//     — only on Clean(B) = { s : B ⊕ Δ_B(s) resolves }
//   Δ_B : Clean(B) -> Im(Δ_B) is a bijection; ⊕_B is its faithful inverse.
//
// PARADOX ROOM (do not close these):
//   P1 (quotient collapse): states equal under canonical order but distinct
//       as raw sequences — Δ_B identifies them; strict-equality backward fails.
//   P2 (ghost zone): diffs in Diff \ Im(Δ_B) — e.g. deletion of a path absent
//       on B — admit no witness state. ⊕ undefined; bijection stops at the image.
//   P3 (D = Δ_D): a diff of the patch-lattice against itself; left open.
//
// BUDGET: total kernel footprint stays far under 1 MiB; all closures are
// cap-bounded; no unbounded enumeration is ever constructed at runtime.

export type Tree = Record<string, string>;
export type Diff = Record<string, string | null>;

export const canon = (t: Record<string, unknown>) =>
  JSON.stringify(Object.fromEntries(Object.keys(t).sort().map(k => [k, t[k]])));
export const eqTree = (a: Tree, b: Tree) => canon(a) === canon(b);
export const eqDiff = (a: Diff, b: Diff) => canon(a) === canon(b);

export function diff(Tp: Tree, Tc: Tree): Diff {
  const d: Diff = {};
  for (const p of new Set([...Object.keys(Tp), ...Object.keys(Tc)])) {
    if (!(p in Tp)) d[p] = Tc[p];
    else if (!(p in Tc)) d[p] = null;
    else if (Tp[p] !== Tc[p]) d[p] = Tc[p];
  }
  return d;
}

export type Res = { ok: true; tree: Tree } | { ok: false; conflicts: string[] };

export function replay(T: Tree, d: Diff): Res {
  const t: Tree = { ...T }; const cf: string[] = [];
  for (const [p, b] of Object.entries(d)) {
    if (b === null) { if (!(p in t)) cf.push(p); else delete t[p]; }
    else t[p] = b;
  }
  return cf.length ? { ok: false, conflicts: cf } : { ok: true, tree: t };
}

export const isClean = (B: Tree, s: Tree) => replay(B, diff(B, s)).ok;

// exactness: bijection Clean(B) ≅ Im(Δ_B), witnessed both ways
export function forward(B: Tree, s1: Tree, s2: Tree): boolean {
  return !eqTree(s1, s2) || eqDiff(diff(B, s1), diff(B, s2));
}
export function backward(B: Tree, s1: Tree, s2: Tree): boolean {
  return !eqDiff(diff(B, s1), diff(B, s2)) || (!isClean(B, s1) && !isClean(B, s2)) || eqTree(s1, s2);
}
export function roundTrip(B: Tree, s: Tree): boolean {
  const r = replay(B, diff(B, s));
  return r.ok && eqTree(r.tree, s);
}