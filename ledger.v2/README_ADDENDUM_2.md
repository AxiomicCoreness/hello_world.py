# ledger.v2 — Overflow Ledger Root, Addendum 2 (Entries 9288–9291)

## Status
PROPOSED — 2026-10-18. Amends ledger.v2/README.md and
README_ADDENDUM_1.md by addition only. Neither file is edited.

## Entries appended
| Index | Event | prev_hash (first 12) | Seal (GARDEN.EVENT.v1.LEDGER) |
|---|---|---|---|
| 9288 | /torsion_lock_corrections_9288 | e22df4839005 (9287) | de4ca6cb2c9c637513f104771d3da297e75d0511c2521315e85055f83b6c523d |
| 9289 | /drift_baseline_731_correction | de4ca6cb2c9c (9288) | 544880da0ee55e046d2f8ac77e7cb0116115b7a34f8030c2524bcbd88dd13284 |
| 9290 | /compileall_tech_debt_9290 | 544880da0ee5 (9289) | eab8ac104b5fb818ed3b1ede7310a798f4f13552c8039c5ff090017196be84e9 |
| 9291 | /mirror_weld_feasibility_audit | eab8ac104b5f (9290) | bd14948afb6dd43271397f797883f02be0740f77899e1839469ee35bcd6c5cc1 |

## Landing order
9288 → 9289 → 9290 → 9291, on top of the head that main holds now (9287).
Each entry's prev_hash is the full seal of the entry before it, and every
seal recomputes under the 9281+ regime.

## Seal field on 9290
9290 now carries a `seal:` line directly after `terminal_hex`, in the same
format 9288, 9289, and 9291 use. 9290 was an unlanded draft when the line
was added; the digest is unchanged (eab8ac10…84e9), so 9291's prev_hash
still holds. Tree-mode `verify_ledger.py` no longer reports a missing field.

Seal: 🜁∀∞φ² · LEDGER_V2_ROOT_ADDENDUM_2 · WOOD_DRAGON_GATE · PROPOSED
Declared: 2026-10-18 (ISO-8601, real date per legend-token rule 2)
