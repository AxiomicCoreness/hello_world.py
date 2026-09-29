#!/usr/bin/env luajit
-- =============================================================================
-- BPF RING BUFFER SATURATION BENCHMARK AND BARRIER-COST HARNESS
-- =============================================================================
-- Usage:
--   luajit scripts/benchmark_ringbuf.lua [duration_sec] [ring_fd] [max_entries]
--
-- Modes:
--   1. Barrier microbenchmark — always runs. Times N calls of the resolved
--      barrier (exposed as consumer.barrier_src) to quantify the per-call
--      cost of the fallback chain (__sync_synchronize vs membarrier vs
--      sched_yield). This is the honest measure of the context-switch tax:
--      sched_yield-mode barrier cost IS the tax.
--   2. Ring saturation — runs when a ring_fd is passed. Attaches the
--      consumer to an existing BPF_MAP_TYPE_RINGBUF (created by the
--      sys_enter_write producer, scripts/ringbuf_test.bpf.c) and soaks
--      records for the duration. Requires the producer loaded and attached.
--
-- Timing: clock_gettime(CLOCK_MONOTONIC) via FFI — sub-microsecond, no
-- luasocket dependency. os.clock() is NOT used anywhere: it reports process
-- CPU time, not wall time, and would silently corrupt every rate metric.
--
-- Discard accounting: the consumer module does not emit a "DISCARDED"
-- sentinel (comparing cdata to a string is always false). Discards are
-- counted by monitoring the position advance: delta_positions - delivered
-- records = skipped (discard + padding) slots.

local ffi = require("ffi")

ffi.cdef[[
    struct timespec { long tv_sec; long tv_nsec; };
    int clock_gettime(int clk_id, struct timespec *tp);
    int sched_yield(void);
]]

local C = ffi.C
local CLOCK_MONOTONIC = 1

local function now_seconds()
    local ts = ffi.new("struct timespec")
    C.clock_gettime(CLOCK_MONOTONIC, ts)
    return tonumber(ts.tv_sec) + tonumber(ts.tv_nsec) * 1e-9
end

-- Load the hardened consumer module from the same directory tree.
local script_dir = arg and arg[0] and arg[0]:match("^(.*)/") or "."
local Ringbuf = dofile(script_dir .. "/ebpf_ringbuf.lua")

local duration   = tonumber(arg and arg[1]) or 5.0
local ring_fd    = tonumber(arg and arg[2]) or -1
local max_entries = tonumber(arg and arg[3]) or 256 * 1024

-- ─────────────────────────────────────────────────────────────────────────────
-- Barrier microbenchmark
-- ─────────────────────────────────────────────────────────────────────────────
-- We time the equivalent call of the RESOLVED mechanism (module's
-- barrier_src drives the dispatch), replicating the same call path the
-- consumer hot loop uses, so the measurement is representative.

local function barrier_call_by_src(src)
    if src == "__sync_synchronize" then
        local ok = pcall(function() C.__sync_synchronize() end)
        if ok then return function() C.__sync_synchronize() end end
    end
    if src == "membarrier(PRIVATE_EXPEDITED)" then
        return function()
            local r = C.syscall(324, 4)
            if r ~= 0 then error("membarrier failed") end
        end
    end
    return function() C.sched_yield() end
end

local function run_barrier_microbench()
    print("=============================================================================")
    print("BARRIER RESOLUTION MICROBENCHMARK")
    print("=============================================================================")
    print("Resolved barrier mechanism: " .. tostring(Ringbuf.barrier_src))

    local src = Ringbuf.barrier_src or "sched_yield"
    local barrier = barrier_call_by_src(src)

    local N = 1000000
    -- Baseline: empty loop with anti-DCE sink
    local t0 = now_seconds()
    local sink = 0
    for i = 1, N do sink = sink + (i & 1) end
    local t_base = now_seconds() - t0

    -- Barrier loop
    local t1 = now_seconds()
    for _ = 1, N do barrier() end
    local t_bar = now_seconds() - t1

    local per_call_ns = (t_bar - t_base) / N * 1e9
    print(string.format("Baseline loop (%d iters)      : %.3f s", N, t_base))
    print(string.format("Barrier loop  (%d iters)      : %.3f s", N, t_bar))
    print(string.format("Per-barrier cost (net)        : %.1f ns  (%.2f M barriers/sec)",
        per_call_ns, 1 / (per_call_ns / 1e9) / 1e6))
    print(string.format("Loop-sink checksum (anti-DCE) : %d", sink))
    if per_call_ns > 1000 then
        print("NOTE: per-barrier cost > 1 usec — consistent with a syscall-backed")
        print("      barrier (membarrier/sched_yield). On x86-64 TSO the fence is")
        print("      ~free at the hardware level; this cost is the fallback chain,")
        print("      not the architecture. A dmb ishld/ishst C shim would remove it.")
    end
    print("=============================================================================")
    return per_call_ns
end

-- ─────────────────────────────────────────────────────────────────────────────
-- Ring saturation soak
-- ─────────────────────────────────────────────────────────────────────────────
local function run_saturation(duration, fd, entries)
    print(string.format("[*] Attaching consumer to ring fd %d (max_entries=%d)...",
        fd, entries))
    local ring = Ringbuf:new(fd, entries)
    print("[+] Attached. Soaking under kernel write pressure for "
        .. string.format("%.1f", duration) .. "s...")

    local valid = 0
    local bytes = 0
    local milestones = 0
    local skipped = 0
    local last_pos = tonumber(ring.cons_pos_ptr[0])

    local t0 = now_seconds()
    local t_end = t0 + duration

    while now_seconds() < t_end do
        local delivered = ring:poll(function(ptr, len)
            valid = valid + 1
            bytes = bytes + len
            -- milestone tag: first byte == 1 (see ringbuf_test.bpf.c)
            if len >= 16 then
                local b = ffi.cast("uint8_t*", ptr)
                if b[0] == 1 then milestones = milestones + 1 end
            end
        end)
        -- Skip accounting via position delta: each delivered record
        -- consumes exactly 24 bytes of stride (8-byte header + 13-byte
        -- payload + alignment). Anything beyond delivered*24 is discard
        -- or padding slots.
        local now_pos = tonumber(ring.cons_pos_ptr[0])
        local advanced = now_pos - last_pos
        last_pos = now_pos
        skipped = skipped + math.max(0, math.floor(advanced / 24) - delivered)
    end

    local elapsed = now_seconds() - t0
    local total_ops = valid + skipped

    print("")
    print("=============================================================================")
    print("SATURATION HARNESS TELEMETRY")
    print("=============================================================================")
    print(string.format("Elapsed (wall, CLOCK_MONOTONIC) : %.6f s", elapsed))
    print(string.format("Valid records consumed         : %d  (%.0f recs/sec)",
        valid, valid / elapsed))
    print(string.format("Skipped slots (discard+pad)    : %d  (%.0f skips/sec)",
        skipped, skipped / elapsed))
    print(string.format("Milestone-tagged records       : %d", milestones))
    print(string.format("Aggregated frame velocity       : %.0f ops/sec", total_ops / elapsed))
    print(string.format("Sustained payload bandwidth     : %.3f MB/sec",
        bytes / (1024 * 1024) / elapsed))
    print("=============================================================================")

    ring:destroy()
    return total_ops / elapsed
end

-- ─────────────────────────────────────────────────────────────────────────────
-- Main
-- ─────────────────────────────────────────────────────────────────────────────
run_barrier_microbench()
print("")
if ring_fd >= 0 then
    run_saturation(duration, ring_fd, max_entries)
else
    print("[!] No ring_fd passed (arg 2). Saturation soak SKIPPED.")
    print("    Load the producer first (scripts/ringbuf_test.bpf.c), obtain the")
    print("    ring map fd, then: luajit scripts/benchmark_ringbuf.lua 5 <fd> 262144")
    print("    Only the barrier microbenchmark ran.")
end
