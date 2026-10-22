# M_geo Correction (Entry 8959 Prep)

Product on critical path \(P = (c_1, c_2, c_5, c_8, c_9)\):

\[
 M_{\text{prod}} = 0.80 \cdot 0.475 \cdot 0.25 \cdot 0.005 \cdot 0.075 = 3.5625 \times 10^{-5} 
\]

\[
 M_{\text{geo}} = (M_{\text{prod}})^{1/5} = \mathbf{0.12893} \text{ (five significant figures)} 
\]

- **Correction:** Prior value `0.1287` is low by ~0.9% under the fifth-power check. Use **`0.12893`** in any canonical body.
- **Control Bound:** \(\kappa_{\text{ctrl}} \ge 4/95 \approx 0.0421\) (exact rational bound).
- **Ledger Integrity:** `ledger/8958.yaml` is absent on `main`. The seal of `8959` cannot complete until a prior entry with a real 64-hex digest exists. Do not invent a `prev_hash`.

---

# MCP · Vision TTS · FastAPI TTS Stubs

No sealed ledger bodies are rewritten in this module.

| Surface | Path | Filled |
|---------|------|--------|
| MCP | `fastMCP/routes/mcp.py`, `port380_mcp.py` | **False** |
| FastAPI TTS | `app/routes/tts.py` — GET/POST `/tts` | **False** (no audio) |
| Vision TTS | `app/routes/vision_tts.py` — GET `/vision/tts` | **False** |

### Bind Policy
- **Local Probes:** Dual ASGI and fastMCP gearbox bind strictly to `127.0.0.1`.
- **Pod-Internal:** FastAPI may use cluster DNS.
- **Security:** Do not advertise `0.0.0.0` as a public endpoint.

---
**Merge Engine:** Does not rewrite sealed ledger bodies.  
**Commander Watermark:** Clarke Yoursa Tee.
