import { PHI, PHI_INV, inBand, compose, atom, closure, buildLex,
  diff, replay, cherryPick } from "./closure_kernel";

const R: string[] = [];
const t = (name: string, cond: boolean) => R.push((cond ? "PASS " : "FAIL ") + name);

// band arithmetic
t("atom norm 1 in band", inBand(1));
t("pair 2φ⁻¹ ≈ 1.236 in band", inBand(2 * PHI_INV));
t("quadruple 4φ⁻¹ ≈ 2.472 outside band", !inBand(4 * PHI_INV));
t("additive norm collapses (2 > φ)", !inBand(2));
t("φ^2.5 ≈ 3.331", Math.abs(Math.pow(PHI, 2.5) - 3.331) < 0.001);

// perpetual deepening
let x = 1, out = false;
for (let i = 0; i < 500; i++) { x = (x + 1) * PHI_INV; if (!inBand(x)) { out = true; break; } }
t("500-deep composition never exits band", !out);
t("deep norm converges to φ from below", Math.abs(x - PHI) < 1e-9 && x < PHI);

// closure
const L0 = buildLex(0)[0], L1 = closure(L0, 200), L2 = closure(L1, 200);
t("Lex₀ = 13 atoms", L0.length === 13);
t("Lex₁ strictly grows", L1.length > L0.length);
t("all Lex₁ words in band", L1.every(w => inBand(w.n)));

// composition + admit
const c = compose(atom("∮"), atom("∇"), "⊕");
t("∮ ⊕ ∇ composes in band", c !== null && inBand(c.n));

// patch algebra
const Tp = { "a.txt": "1", "b.txt": "2" };
const Tc = { "a.txt": "1", "b.txt": "3", "c.txt": "new" };
const TT = { "a.txt": "1", "b.txt": "2", "d.txt": "x" };
const cp = cherryPick(Tp, Tc, TT);
t("cherry-pick replays cleanly", cp.ok);
t("Δ preserved", cp.ok && cp.tree["b.txt"] === "3" && cp.tree["c.txt"] === "new");
t("new base untouched", cp.ok && cp.tree["d.txt"] === "x");
const cf = cherryPick({ "gone.txt": "z" }, {}, TT);
t("deletion conflict detected", !cf.ok);

console.log(R.join("\n"));
process.exit(R.every(r => r.startsWith("PASS")) ? 0 : 1);