# Pointer history rewire

Reader-side only. Sealed ledger files were not edited.

forms: {'immediate': 776, 'span': 136, 'skip': 14, 'rewired': 26}

## Rewired numeric siblings — DERIVED, not stored

These 26 links are reader assertions. The files do not carry them. 0365.yaml has no arrow. The old `8513 → 8514` hit is in 0366.yaml, the successor, and is not a pointer for index 365.

- 350 -> 351
- 351 -> 352
- 352 -> 353
- 353 -> 354
- 354 -> 355
- 355 -> 356
- 356 -> 357
- 357 -> 358
- 358 -> 359
- 359 -> 360
- 360 -> 361
- 361 -> 362
- 362 -> 363
- 363 -> 364
- 364 -> 365
- 365 -> 366
- 366 -> 367
- 367 -> 368
- 368 -> 369
- 369 -> 370
- 516 -> 517
- 517 -> 518
- 8530 -> 8531
- 8617 -> 8618
- 8734 -> 8735
- 8852 -> 8853

## Form counts

| Form | Example | Count |
|---|---|---|
| immediate pair | 9264 → 9265 | 776 |
| span | stored reference ahead of successor | 136 |
| skip | pair with missing intermediates | 14 |
| rewired, derived | 365 → 366 | 26 |
| boolean flag | Witness_Chain_Unbroken = TRUE | 1 |
| stored cross-statement | Witness_Continuity = 8513 → 8514 — UNBROKEN | 1, ledger/0366.yaml |

The boolean flag is in ledger/0365.yaml. It is not an arrow. The cross-statement is in the successor, not in 0365. Derived links are not stored.
