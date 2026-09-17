# Review polish (9194)

Non-blocking comments. Does not rewrite ledger/9167.yaml–ledger/9193.yaml.

1. Event hash ASCII: `ledger/event_hash.py` uses `phi2`, `delta`, `theta` in the payload string. Unicode φ, Δ, θ are not part of the hash bytes.
2. `verify_math_framework.py` may skip strict seal-hex on some historic ranges. That skip is presence/invariant CI, not a rewrite permit.
3. `requirements-control.txt` is the **offline** minimum (9164). `requirements.txt` is the fuller runtime list. DeepSeek extras do not belong in control.
4. Codespace packing (already in `k8s/codespace/MATH.md`):
   start-class request = 2 vCPU / 4 Gi; test C = 4 vCPU / 8 Gi; two start-class workspaces saturate test requests.
