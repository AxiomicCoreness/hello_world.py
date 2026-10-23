package com.fruitfly.games.rhythm.logic;

import java.util.ArrayList;
import java.util.List;

/**
 * The moves list: one {@link Move} per note, in chart order, written once
 * the note is judged and its fly cue window has closed. Pure logic; the web
 * layer calls {@link #update} every frame and exposes the rows read-only as
 * window.__rhythmDebug.
 *
 * Rules (also in README.md, "Moves list"):
 * <ul>
 *   <li>who: "fly" if a fly spike judged the note, "you" if a key press did,
 *       "none" for a MISS.</li>
 *   <li>Decision value d. Fly modes, rows not taken by you: margin =
 *       V_peak - V_thresh, the lane motor neuron's peak pre-reset membrane
 *       voltage in the cue window minus its threshold (both rounded to
 *       0.001 mV first). Otherwise (you, or no fly): the timing score
 *       (150 - |dt|) / 150, 0 for a MISS.</li>
 *   <li>Chain per lane: chain = previous chain in that lane + 1 on a hit,
 *       0 on a MISS. f(chain) = 1 + min(chain, 10) / 10, so 1.0 .. 2.0.</li>
 *   <li>value = d * f(chain), rounded to 0.001 half away from zero.</li>
 *   <li>Hash chain: hash = SHA-256(preimage) over
 *       {@link Move#preimage}, which includes the previous row's hash
 *       (genesis: 64 zeros) and the math_origin segment.</li>
 * </ul>
 * Bounded memory: the first {@link #FIRST} rows and a ring of the last
 * {@link #RING} rows are kept.
 */
public final class MovesLog {
    public static final int RING = 64;
    public static final int FIRST = 20;
    public static final String GENESIS = "0000000000000000000000000000000000000000000000000000000000000000";
    /** A row is written this long after its note time (95 ms assist aim + 150 ms window + one 50 ms tick). */
    public static final long SETTLE_MS = AssistArbiter.FLY_AIM_MS + Judgement.MAX_WINDOW_MS + (long) LifNeuron.BRAIN_TICK_MS;
    public static final long TH_MILLI = Math.round(LifNeuron.V_THRESH * 1000.0);

    private final RhythmGame game;
    private final int mode;
    private final CueProbe probe;
    private final int[] chain = new int[RhythmGame.LANES];
    private final List<Move> first = new ArrayList<>();
    private final Move[] ring = new Move[RING];
    private int written;
    private int next;
    private String lastHash = GENESIS;

    /** @param probe the active fly brain's probe, or null when no fly plays (mode OFF). */
    public MovesLog(RhythmGame game, int mode, CueProbe probe) {
        this.game = game;
        this.mode = mode;
        this.probe = probe;
    }

    public int mode() {
        return mode;
    }

    /** Write every row whose note is judged and settled by song time {@code songMs} (all judged ones once the song is finished). Returns the new rows. */
    public List<Move> update(long songMs) {
        List<Note> notes = game.chart().notes();
        List<Move> out = new ArrayList<>();
        boolean all = game.isFinished();
        while (next < notes.size()) {
            Note n = notes.get(next);
            if (!n.isResolved() || (!all && songMs < n.timeMs() + SETTLE_MS)) {
                break;
            }
            Move m = build(next, n, next == 0 ? Move.NA : n.timeMs() - notes.get(next - 1).timeMs());
            append(m);
            out.add(m);
            next++;
        }
        return out;
    }

    private Move build(int idx, Note n, long delta) {
        boolean hit = n.result() != Judgement.MISS;
        String who = !hit ? "none" : n.actor() == Note.ACTOR_FLY ? "fly" : "you";
        long press = hit ? n.judgedAtMs() : Move.NA;
        long dt = hit ? press - n.timeMs() : Move.NA;
        long v = Move.NA;
        long th = Move.NA;
        long fired = Move.NA;
        long lat = Move.NA;
        boolean cued = probe != null && idx < probe.size() && probe.wasCued(idx);
        if (probe != null) {
            fired = cued && probe.fired(idx) ? 1 : 0;
            if (cued) {
                v = Math.round(probe.peakV(idx) * 1000.0);
                th = TH_MILLI;
                if (probe.fired(idx)) {
                    lat = probe.spikeMs(idx) - probe.cueMs(idx);
                }
            }
        }
        chain[n.lane()] = hit ? chain[n.lane()] + 1 : 0;
        String kind;
        long d;
        if (cued && !"you".equals(who)) {
            kind = Move.KIND_MARGIN;
            d = v - th;
        } else {
            kind = Move.KIND_TIMING;
            d = Move.timingScoreMilli(dt);
        }
        return new Move(idx, n.timeMs(), n.lane(), delta, who, press, dt, n.result().name(),
                v, th, fired, lat, kind, d, chain[n.lane()], lastHash);
    }

    private void append(Move m) {
        if (first.size() < FIRST) {
            first.add(m);
        }
        ring[written % RING] = m;
        written++;
        lastHash = m.hash;
    }

    /** Rows written so far (the chain length). */
    public int size() {
        return written;
    }

    public String lastHash() {
        return lastHash;
    }

    /** The first {@link #FIRST} rows. */
    public List<Move> first20() {
        return new ArrayList<>(first);
    }

    /** The last {@link #RING} rows, oldest first. */
    public List<Move> recent() {
        List<Move> r = new ArrayList<>();
        int from = Math.max(0, written - RING);
        for (int k = from; k < written; k++) {
            r.add(ring[k % RING]);
        }
        return r;
    }

    /** The last {@code n} rows, oldest first. */
    public List<Move> tail(int n) {
        List<Move> r = recent();
        return r.subList(Math.max(0, r.size() - n), r.size());
    }

    /** Re-derive math_origin and the hash chain over the kept rows; -1 if all good, else the note index of the first bad row. */
    public int verifyKept() {
        int bad = verify(first);
        if (bad >= 0) {
            return bad;
        }
        List<Move> r = recent();
        bad = verify(r);
        if (bad >= 0) {
            return bad;
        }
        // the two segments overlap or touch: the join must link too
        if (!r.isEmpty() && !first.isEmpty() && r.get(0).i <= first.get(first.size() - 1).i + 1) {
            for (Move m : r) {
                if (m.i == first.get(first.size() - 1).i + 1 && !m.prev.equals(first.get(first.size() - 1).hash)) {
                    return m.i;
                }
            }
        }
        return -1;
    }

    /**
     * Verify consecutive rows: each row's math_origin re-derived from its
     * fields, its hash re-computed from its preimage, and each prev equal to
     * the row before (row 0 of the song: the genesis hash). Returns -1 or the
     * note index of the first bad row.
     */
    public static int verify(List<Move> rows) {
        for (int k = 0; k < rows.size(); k++) {
            Move m = rows.get(k);
            if (m.fTenths != Move.chainFactorTenths(m.chain) || m.valueMilli != Move.value(m.dMilli, m.fTenths)) {
                return m.i;
            }
            if (Move.KIND_MARGIN.equals(m.kind) && m.dMilli != m.vMilli - m.thMilli) {
                return m.i;
            }
            if (Move.KIND_TIMING.equals(m.kind) && m.dMilli != Move.timingScoreMilli(m.dt)) {
                return m.i;
            }
            if (!m.mathOrigin.equals(Move.mathOrigin(m))) {
                return m.i;
            }
            String expectPrev = k > 0 ? rows.get(k - 1).hash : m.i == 0 ? GENESIS : m.prev;
            if (!m.prev.equals(expectPrev)) {
                return m.i;
            }
            if (!m.hash.equals(Sha256.hex(Move.preimage(m, m.prev)))) {
                return m.i;
            }
        }
        return -1;
    }

    public static String toJson(List<Move> rows) {
        StringBuilder b = new StringBuilder("[");
        for (int k = 0; k < rows.size(); k++) {
            if (k > 0) {
                b.append(',');
            }
            b.append(rows.get(k).toJson());
        }
        return b.append(']').toString();
    }
}
