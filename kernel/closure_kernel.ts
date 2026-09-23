// ─── golden-section closure kernel · φ-band admit · Δ-replay ───────────────
// Invariants:
//   band           : φ⁻¹ < ‖w‖ < φ            (strict, open)
//   atom norm      : ‖t‖ = 1                   (geometric self-dual point of the band)
//   composition    : ‖w₀ ⊕ w₁‖ = ‖w₀ ⊗ w₁‖ = (‖w₀‖ + ‖w₁‖)·φ⁻¹
//   deepening      : x ↦ (x+1)φ⁻¹ is a contraction with fixed point φ,
//                    approached from below — words compose forever without
//                    leaving the band (perpetual deepening).
// Patch law:
//   Δ(c) = T_c − T_p ;  c' = commit(parent = T, tree = T_T ⊕ Δ(c))
//   ⊕ is partial: deletion of a path absent on T_T is a conflict.

export const PHI = (1 + Math.sqrt(5)) / 2;
export const PHI_INV = 1 / PHI;
export const ATOM_NORM = 1;
export const inBand = (n: number) => PHI_INV < n && n < PHI;

export type Op = "⊕" | "⊗";
export interface Word { readonly k: string; readonly n: number; }

export const atom = (t: string): Word => ({ k: t, n: ATOM_NORM });

export function compose(a: Word, b: Word, op: Op): Word | null {
  const n = (a.n + b.n) * PHI_INV;
  if (!inBand(n)) return null;
  return { k: "(" + a.k + op + b.k + ")", n };
}

// Lex_{n+1} = Lex_n ∪ { w₀ op w₁ | φ⁻¹ < ‖w₀ op w₁‖ < φ }   (cap-bounded)
export function closure(lex: Word[], cap = 200): Word[] {
  const out = [...lex];
  const seen = new Set(out.map(w => w.k));
  outer:
  for (const a of lex) for (const b of lex) for (const op of ["⊕", "⊗"] as Op[]) {
    const c = compose(a, b, op);
    if (!c) continue;
    if (!seen.has(c.k)) { seen.add(c.k); out.push(c); }
    if (out.length >= cap) break outer;
  }
  return out;
}

export function buildLex(depth: number, cap = 200): Word[][] {
  const atoms = ["∀","φ","|","⟩","⟨","⊕","⊗","∮","∂","∫","∇","·","×"].map(atom);
  const levels: Word[][] = [atoms];
  for (let i = 0; i < depth; i++) levels.push(closure(levels[i], cap));
  return levels;
}

// admit(w) := band(w) ∧ w ∉ ideal(prior) at bounded composition depth K
export function admit(w: Word, prior: Word[], K = 2): boolean {
  if (!inBand(w.n)) return false;
  const byKey = new Map<string, number>(prior.map(p => [p.k, p.n]));
  for (let d = 0; d < K; d++) {
    const keys = [...byKey.keys()];
    let grew = false;
    for (const ka of keys) for (const kb of keys) {
      const a: Word = { k: ka, n: byKey.get(ka)! };
      const b: Word = { k: kb, n: byKey.get(kb)! };
      for (const op of ["⊕", "⊗"] as Op[]) {
        const c = compose(a, b, op);
        if (!c) continue;
        if (!byKey.has(c.k)) { byKey.set(c.k, c.n); grew = true; }
      }
    }
    if (byKey.has(w.k)) return false;
    if (!grew) break;
  }
  return true;
}

// ─── patch algebra ──────────────────────────────────────────────────────────
export type Tree = Record<string, string>;
export type Diff = Record<string, string | null>; // null = deletion
export type MergeResult = { ok: true; tree: Tree } | { ok: false; conflicts: string[] };

export function diff(Tp: Tree, Tc: Tree): Diff {
  const d: Diff = {};
  for (const p of new Set([...Object.keys(Tp), ...Object.keys(Tc)])) {
    if (!(p in Tp)) d[p] = Tc[p];
    else if (!(p in Tc)) d[p] = null;
    else if (Tp[p] !== Tc[p]) d[p] = Tc[p];
  }
  return d;
}

export function replay(T: Tree, d: Diff): MergeResult {
  const t: Tree = { ...T };
  const conflicts: string[] = [];
  for (const [p, blob] of Object.entries(d)) {
    if (blob === null) { if (!(p in t)) conflicts.push(p); else delete t[p]; }
    else t[p] = blob;
  }
  return conflicts.length ? { ok: false, conflicts } : { ok: true, tree: t };
}

// c' = commit(parent = T, tree = T_T ⊕ Δ(c)) — same Δ, new base, fresh identity
export function cherryPick(Tp: Tree, Tc: Tree, TT: Tree): MergeResult & { delta?: Diff } {
  const delta = diff(Tp, Tc);
  const r = replay(TT, delta);
  return r.ok ? { ...r, delta } : r;
}