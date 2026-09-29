-- ebpf_ringbuf.lua — BPF_MAP_TYPE_RINGBUF consumer for LuaJIT
-- VMA layout (kernel/libbpf):
--   offset 0        : consumer page   (PROT_READ|PROT_WRITE)
--   offset PAGE     : producer page   \  one shared RO mapping,
--   offset 2*PAGE   : data area (2*max_entries bytes)  /
-- libbpf does TWO mmaps: consumer page RW, then (producer + data) as one
-- RO mapping of length PAGE + 2*max_entries. A single mmap cannot mix
-- protections, so two is the minimum.
--
-- PLATFORM SCOPE: x86-64 ONLY, as written. On arm64 the producer_pos load
-- needs acquire and the consumer_pos store needs release ordering; plain
-- LuaJIT FFI loads/stores do NOT provide these. A syscall return
-- (epoll_wait etc.) is a full barrier on x86 but does NOT confer acquire
-- semantics on arm64. To run on arm64, add a C shim exposing
-- __atomic_load_n(p, __ATOMIC_ACQUIRE) / __atomic_store_n(p, v, __ATOMIC_RELEASE)
-- and route _next_record/advance through it. The x86 test suite cannot
-- detect the absence of these barriers; only arm64 hardware or a weakly
-- ordered simulator can.

local ffi = require("ffi")
local bit = require("bit")

ffi.cdef[[
    union bpf_attr {
        struct { uint32_t map_type; uint32_t key_size; uint32_t value_size;
                 uint32_t max_entries; uint32_t map_flags; };
        // PROG_LOAD / LINK_CREATE arms omitted — see ebpf.lua
    };
    void *mmap(void *addr, size_t len, int prot, int flags, int fd, long off);
    int munmap(void *addr, size_t len);
    int bpf(int cmd, union bpf_attr *attr, unsigned int size);
    int close(int fd);
    int sched_yield(void);
]]

local C = ffi.C
local BPF_MAP_CREATE, BPF_MAP_TYPE_RINGBUF = 0, 27
local PROT_READ, PROT_WRITE, MAP_SHARED = 0x1, 0x2, 0x01

local PAGE = 4096

-- Record header flag bits (kernel: include/uapi/linux/bpf.h).
-- Held as uint32_t cdata: 0x80000000 as a plain Lua number is > 2^31, and
-- LuaJIT's number->int32 conversion for bitwise ops is implementation-
-- defined at that magnitude. cdata & cdata keeps everything in uint32_t.
local BUSY_BIT    = ffi.cast("uint32_t", 0x80000000)
local DISCARD_BIT = ffi.cast("uint32_t", 0x40000000)
local LEN_MASK    = ffi.cast("uint32_t", 0x3fffffff)
local U64_SEVEN   = ffi.new("uint64_t", 7)

local MAP_FAILED = ffi.cast("void*", 0xFFFFFFFFFFFFFFFFULL)

local Ringbuf = {}
Ringbuf.__index = Ringbuf

function Ringbuf.create(max_entries)
    local attr = ffi.new("union bpf_attr")
    attr.map_type    = BPF_MAP_TYPE_RINGBUF
    attr.key_size    = 0
    attr.value_size  = 0
    attr.max_entries = max_entries
    attr.map_flags   = 0
    local fd = C.bpf(BPF_MAP_CREATE, attr, ffi.sizeof("union bpf_attr"))
    if fd < 0 then error("BPF_MAP_CREATE: errno " .. tostring(ffi.errno())) end
    return fd
end

function Ringbuf:new(map_fd, max_entries)
    -- All position arithmetic in uint64_t cdata, never Lua doubles.
    local data_size = ffi.new("uint64_t", max_entries)
    local prod_map_len = PAGE + 2 * max_entries

    -- Two mmaps, libbpf-style:
    --   1. consumer page, RW, offset 0
    --   2. producer page + data area, RO, offset PAGE, length PAGE + 2*max
    local cons_map = C.mmap(nil, PAGE, bit.bor(PROT_READ, PROT_WRITE),
                            MAP_SHARED, map_fd, 0)
    local prod_map = C.mmap(nil, prod_map_len, PROT_READ,
                            MAP_SHARED, map_fd, PAGE)

    if cons_map == MAP_FAILED or prod_map == MAP_FAILED then
        if cons_map ~= MAP_FAILED then C.munmap(cons_map, PAGE) end
        if prod_map ~= MAP_FAILED then C.munmap(prod_map, prod_map_len) end
        error("mmap failed: errno " .. tostring(ffi.errno()))
    end

    local base = ffi.cast("char*", prod_map)
    local o = setmetatable({
        fd           = map_fd,
        cons_map     = cons_map,
        prod_map     = prod_map,
        prod_map_len = prod_map_len,
        data_size    = data_size,                        -- uint64_t cdata
        cons_pos_ptr = ffi.cast("uint64_t*", cons_map),
        prod_pos_ptr = ffi.cast("uint64_t*", prod_map),  -- producer page at offset 0 of this mapping
        data         = base + PAGE,                      -- data at absolute offset 2*PAGE
    }, self)
    o.cons = o.cons_pos_ptr[0]
    return o
end

-- Header flag tests: all in uint32_t cdata via bit.band.
local function busy(v)    return bit.band(v, BUSY_BIT) ~= 0 end
local function discard(v) return bit.band(v, DISCARD_BIT) ~= 0 end
local function rec_len(v) return tonumber(bit.band(v, LEN_MASK)) end

function Ringbuf:_next_record()
    -- x86-only ordering note: see PLATFORM SCOPE at top of file.
    local prod = self.prod_pos_ptr[0]
    if self.cons >= prod then return nil end

    local hdr = ffi.cast("uint32_t*", self.data + (self.cons % self.data_size))
    local hdr_val = hdr[0]

    -- busy: kernel is mid-write. Yield, do not hot-spin.
    while busy(hdr_val) do
        C.sched_yield()
        hdr = ffi.cast("uint32_t*", self.data + (self.cons % self.data_size))
        hdr_val = hdr[0]
    end

    local len = rec_len(hdr_val)

    -- discard: consume the slot, deliver nothing
    if discard(hdr_val) then
        self.cons = self.cons + ffi.new("uint64_t", 8 + len)
        self.cons = bit.band(self.cons + U64_SEVEN, bit.bnot(U64_SEVEN))
        return self:_next_record()
    end

    if len == 0 then
        -- padding: warp to end of data region
        self.cons = self.cons + (self.data_size - (self.cons % self.data_size))
        return self:_next_record()
    end

    local payload = self.data + (self.cons % self.data_size) + 8
    local rec = { pos = self.cons, len = len, ptr = payload }
    self.cons = self.cons + ffi.new("uint64_t", 8 + len)
    self.cons = bit.band(self.cons + U64_SEVEN, bit.bnot(U64_SEVEN))
    return rec
end

function Ringbuf:poll(handler)
    local n = 0
    while true do
        local rec = self:_next_record()
        if not rec then return n end
        handler(rec.ptr, rec.len)
        n = n + 1
    end
end

function Ringbuf:advance()
    -- Release-store needed on arm64 (C shim); plain store is release on x86.
    self.cons_pos_ptr[0] = self.cons
end

function Ringbuf:destroy()
    C.munmap(self.cons_map, PAGE)
    C.munmap(self.prod_map, self.prod_map_len)
    C.close(self.fd)
end

return Ringbuf
