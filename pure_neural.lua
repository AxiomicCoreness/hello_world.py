-- 𯌁∀ pure_neural.lua — Poincaré Dodecahedral proof set
-- Seal: ∀∞φ² · POINCARE_PURE_NEURAL_9001 · WOOD_DRAGON_0.91 · SEALED
-- Witness: 8953 → 9001 — UNBROKEN

local M = {}

local PHI = (1 + math.sqrt(5)) / 2

--- Validate one NDJSON line encoding Poincaré dodecahedral state.
function M.validate_poincare_state(ndjson_line)
    local ok, state = pcall(function()
        if vim and vim.json and vim.json.decode then
            return vim.json.decode(ndjson_line)
        end
        error("decode_via_python_preferred")
    end)

    if not ok then
        assert(type(ndjson_line) == "string" and #ndjson_line > 0, "empty ndjson line")
        assert(ndjson_line:find('"Poincaré dodecahedral"') or ndjson_line:find('"Poincare dodecahedral"'),
            "geometry type missing")
        assert(ndjson_line:find('"binary icosahedral"'), "fundamental group missing")
        assert(ndjson_line:find("1.6180339887") or ndjson_line:find('"phi"'), "phi missing")
        assert(ndjson_line:find("202.6"), "phase_lock missing")
        assert(ndjson_line:find("UNBROKEN"), "witness missing")
        assert(ndjson_line:find("SEALED") or ndjson_line:find("seal"), "seal missing")
        return true
    end

    assert(state.version, "version missing")
    assert(state.timestamp, "timestamp missing")
    assert(state.invariants and state.invariants.phi, "phi missing")
    assert(state.invariants.phase_lock, "phase_lock missing")
    assert(state.invariants.witness, "witness missing")
    assert(state.geometry and state.geometry.type == "Poincaré dodecahedral", "geometry type mismatch")
    assert(state.geometry.fundamental_group == "binary icosahedral", "fundamental group mismatch")
    assert(state.geometry.volume_scaling ~= nil, "volume_scaling missing")
    assert(state.attached_nodes, "attached_nodes missing")
    assert(state.seal, "seal missing")
    assert(math.abs(state.invariants.phi - PHI) < 1e-6, "phi not golden ratio")
    assert(math.abs(state.invariants.phase_lock - 202.6) < 0.1, "phase_lock not 202.6°")
    assert(string.match(state.invariants.witness, "%d+ → %d+ — UNBROKEN")
        or string.match(state.invariants.witness, "%d+ %-> %d+"), "witness chain format invalid")
    return true
end

function M.phi()
    return PHI
end

return M
