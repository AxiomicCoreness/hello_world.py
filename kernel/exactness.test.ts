import { forward, backward, roundTrip, replay, diff, eqTree } from "./exactness";
const R: string[] = [];
const t = (n: string, c: boolean) => R.push((c ? "PASS " : "FAIL ") + n);
const B = { "x": "1", "y": "2" };
const s1 = { "x": "1", "y": "9", "z": "new" };
const s2 = { "z": "new", "y": "9", "x": "1" };
t("forward: same state (any order) => same diff", forward(B, s1, s2));
t("backward: equal diffs => equal states (clean)", backward(B, s1, s2));
t("round-trip clean", roundTrip(B, s1));
t("round-trip with deletion", roundTrip(B, { "x": "1" }));
const ghost = replay(B, { "ghost": null });
t("P2 paradox: ghost deletion undefined (no witness state)", !ghost.ok);
// P1 paradox left open: Δ_B identifies canon-equal states; strict backward is
// deliberately NOT asserted for raw-sequence equality.
console.log(R.join("\n"));