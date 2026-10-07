# POLICY WARNING

Visible to a security check of `quantum/security`.

- A missing slot file is not a pass.
- The only slot file is `docs/luminara_slot.yaml`. There is no `slots/` directory and no per-minute slot files.
- `role`, `holder`, and `channel` are nested under `slots`. `gamma`, `lambda`, `log`, and `filled_by` stay null.
- `port380_mcp.py` binds `0.0.0.0` and `PORT` default `380`. `127.0.0.1:8024` is a proposed bind, not the live one.
- `garden_surgery/sovereign_automaton_10.06.py` exposes `sovereign_automaton_10_06()`. It takes no text.
- Do not overwrite `quantum/deepseek_mesh/super_symplectic.py` with a slot checker.
- Do not print secrets. Do not treat a label commit as a seal.
