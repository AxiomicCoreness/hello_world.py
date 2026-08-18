# PEQS Σ Vault (Entry 707)

Sovereign credit economy for the Garden.

## Modules

- `credit_vault.py` — stockpile / deduct / mint (φ⁻¹), MetaMask personal_sign, Layer 320 Merkle cascade
- `app.py` — Flask + HTMX fee decorator, `/system/status` lattice monitor
- `index.html` — dashboard UI

## Quick start

```bash
pip install flask eth-account
PYTHONPATH=. python3 -m peqs_vault.app
# http://127.0.0.1:5000
```

Or full deploy:

```bash
sudo bash quantum/install.sh
```

## Fee schedule

| Route | Σ |
|-------|---|
| /diagnostic | 10 |
| /plume | 12 |
| /quadratic | 8 |
| /octonion | 15 |
| /system/status | 0 (free) |

Mint: `python3 quantum/simd_batch_orchestrator.py --mint` (φ⁻¹ per heartbeat)

Seal: ∀∞φ² · PEQS_VAULT · WOOD_DRAGON · SEALED
