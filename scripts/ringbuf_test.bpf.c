// ringbuf_test.bpf.c — ring buffer producer for the LuaJIT consumer test.
//
// Prerequisites on the target machine (the very first thing that stops you):
//   bpftool btf dump file /sys/kernel/btf/vmlinux format c > vmlinux.h
//   (needs bpftool; vmlinux.h must sit in the current directory)
//
// Compile (no -D flags, no extra -I beyond the default and -I.):
//   clang -g -O2 -target bpf -c ringbuf_test.bpf.c -o ringbuf_test.bpf.o
//   (needs clang with BPF target + libbpf-dev for bpf/bpf_helpers.h)
//
// Tracepoint: sys_enter_write. WARNING: this fires on every write() system
// call system-wide — millions/sec on a normal box. That is deliberate:
// we WANT to wrap the 256 KiB ring in under a second. Consequently there
// is NO bpf_printk anywhere in this program — a printk on this path would
// flood the trace buffer. Diagnostics go through the ring itself, gated
// by the counter (one in 4096 records carries a nonzero payload tag).
//
// Record design (13-byte payload, exercising the consumer):
//   - Every 10th record is reserved and then DISCARDED with no memcpy:
//     zero-copy path, tests the consumer's DISCARD_BIT advance-without-
//     -deliver logic. Copying bytes into a buffer you're about to discard
//     tests nothing, so we don't do it.
//   - Every 4096th record carries a tag byte so the consumer can spot-
//     check ordering/liveness without flooding.
//   - 8-byte header + 13-byte payload, consumer rounds to a 24-byte stride.

#include "vmlinux.h"
#include <bpf/bpf_helpers.h>

struct event {
    __u8  tag;        // 0 = plain, 1 = milestone
    __u8  pad[3];
    __u32 pid;
    __u64 ts_ns;
};  // 16 bytes used, 13 reserved (ring pads to alignment anyway)

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} ringbuf SEC(".maps");

SEC("tracepoint/syscalls/sys_enter_write")
int trace_write(struct trace_event_raw_sys_enter *ctx)
{
    static __u64 count = 0;   // BPF per-CPU variable, fixed iteration — no loop
    __u64 n = __sync_fetch_and_add(&count, 1);

    // Every 10th record: reserve then discard, zero-copy, no memcpy.
    if (n % 10 == 0) {
        void *sample = bpf_ringbuf_reserve(&ringbuf, 13, 0);
        if (sample)
            bpf_ringbuf_discard(sample, 0);
        return 0;
    }

    // Milestone every 4096th record: tagged payload for liveness checks.
    if (n % 4096 == 0) {
        struct event *ev = bpf_ringbuf_reserve(&ringbuf, sizeof(*ev), 0);
        if (!ev)
            return 0;
        ev->tag    = 1;
        ev->pid    = bpf_get_current_pid_tgid() >> 32;
        ev->ts_ns  = bpf_ktime_get_ns();
        bpf_ringbuf_submit(ev, 0);
        return 0;
    }

    // Plain record: 13-byte payload, minimal content.
    __u8 *buf = bpf_ringbuf_reserve(&ringbuf, 13, 0);
    if (!buf)
        return 0;
    buf[0] = 0;
    bpf_ringbuf_submit(buf, 0);
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
