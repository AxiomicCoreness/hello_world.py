package com.fruitfly.games.rhythm.logic;

/**
 * One row of the moves list: what happened to one note, modelled like a
 * ledger entry. Every number that the row's value depends on is an integer
 * (ms, or thousandths of a mV / of a score), so the derived fields
 * ({@link #mathOrigin}, {@link #hash}) can be recomputed exactly from the
 * other fields in Java, JavaScript or Python. See {@link MovesLog} for the
 * rules and README.md ("Moves list") for the formula.
 *
 * Absent values are {@link #NA} (JSON null, "na" in the preimage).
 */
public final class Move {
    public static final long NA = Long.MIN_VALUE;
    public static final String KIND_MARGIN = "margin";
    public static final String KIND_TIMING = "timing";

    /** Note index in the chart. */
    public final int i;
    /** Note time, ms. */
    public final long t;
    public final int lane;
    /** t minus the previous note's time in the chart (NA for the first note). */
    public final long delta;
    /** "you", "fly" or "none" (MISS). */
    public final String who;
    /** Press time, ms (NA for a MISS). */
    public final long press;
    /** press - t, ms (NA for a MISS). */
    public final long dt;
    /** PERFECT / GREAT / GOOD / MISS. */
    public final String judge;
    /** Peak pre-reset voltage of the lane motor neuron in the cue window, thousandths of a mV (NA: no fly / not cued). */
    public final long vMilli;
    /** Its threshold, thousandths of a mV (NA when vMilli is NA). */
    public final long thMilli;
    /** 1 = the lane motor neuron spiked in the cue window, 0 = it did not, NA = no fly in this mode. */
    public final long fired;
    /** Cue-to-spike latency, ms (NA unless fired). */
    public final long lat;
    /** {@link #KIND_MARGIN} (fly decision, V - threshold) or {@link #KIND_TIMING} (human timing score). */
    public final String kind;
    /** Decision value, thousandths: margin in mV, or timing score in [0, 1]. */
    public final long dMilli;
    /** Consecutive hits in this lane, this row included (0 after a MISS). */
    public final int chain;
    /** Chain factor f(chain) = 1 + min(chain, 10) / 10, in tenths (10..20). */
    public final int fTenths;
    /** value = d * f(chain), thousandths, rounded half away from zero. */
    public final long valueMilli;
    public final String mathOrigin;
    public final String prev;
    public final String hash;

    Move(int i, long t, int lane, long delta, String who, long press, long dt, String judge,
            long vMilli, long thMilli, long fired, long lat, String kind, long dMilli, int chain,
            String prev) {
        this.i = i;
        this.t = t;
        this.lane = lane;
        this.delta = delta;
        this.who = who;
        this.press = press;
        this.dt = dt;
        this.judge = judge;
        this.vMilli = vMilli;
        this.thMilli = thMilli;
        this.fired = fired;
        this.lat = lat;
        this.kind = kind;
        this.dMilli = dMilli;
        this.chain = chain;
        this.fTenths = chainFactorTenths(chain);
        this.valueMilli = value(dMilli, fTenths);
        this.mathOrigin = mathOrigin(this);
        this.prev = prev;
        this.hash = Sha256.hex(preimage(this, prev));
    }

    /** Copy with one field changed (tests: tamper detection). Derived fields are kept as they were. */
    Move(Move m, String judge, String mathOrigin, String prev, String hash) {
        this.i = m.i;
        this.t = m.t;
        this.lane = m.lane;
        this.delta = m.delta;
        this.who = m.who;
        this.press = m.press;
        this.dt = m.dt;
        this.judge = judge;
        this.vMilli = m.vMilli;
        this.thMilli = m.thMilli;
        this.fired = m.fired;
        this.lat = m.lat;
        this.kind = m.kind;
        this.dMilli = m.dMilli;
        this.chain = m.chain;
        this.fTenths = m.fTenths;
        this.valueMilli = m.valueMilli;
        this.mathOrigin = mathOrigin;
        this.prev = prev;
        this.hash = hash;
    }

    public String key() {
        return RhythmGame.LANE_KEYS[lane];
    }

    /** f(chain) = 1 + min(chain, 10) / 10, as tenths: 10 (chain 0) .. 20 (chain 10 or more). */
    public static int chainFactorTenths(int chain) {
        return 10 + Math.min(Math.max(chain, 0), 10);
    }

    /** round(d * fTenths / 10), half away from zero, in integers. */
    public static long value(long dMilli, int fTenths) {
        long v = dMilli * fTenths;
        return v >= 0 ? (v + 5) / 10 : -((-v + 5) / 10);
    }

    /** Timing score in thousandths: round(1000 * (150 - |dt|) / 150) for a hit, 0 for a MISS (NA dt). */
    public static long timingScoreMilli(long dt) {
        if (dt == NA) {
            return 0;
        }
        long a = Math.min(Math.abs(dt), Judgement.MAX_WINDOW_MS);
        return (2000 * (Judgement.MAX_WINDOW_MS - a) + Judgement.MAX_WINDOW_MS) / (2 * Judgement.MAX_WINDOW_MS);
    }

    /** Thousandths as fixed 3-decimal text: -45000 -> "-45.000", 188 -> "0.188", -5 -> "-0.005". */
    public static String fixed3(long milli) {
        if (milli == NA) {
            return "na";
        }
        boolean neg = milli < 0;
        long a = Math.abs(milli);
        long frac = a % 1000;
        String f = frac < 10 ? "00" + frac : frac < 100 ? "0" + frac : String.valueOf(frac);
        return (neg ? "-" : "") + (a / 1000) + "." + f;
    }

    static String num(long v) {
        return v == NA ? "na" : String.valueOf(v);
    }

    /**
     * The derived segment, in the style of math_origin.py's payload_segment:
     * margin rows "math_origin=Decision(t=..;lane=..;who=..;V=..;th=..;margin=..;chain=..;f=..;value=..)",
     * timing rows "math_origin=Decision(t=..;lane=..;who=..;dt=..;score=..;chain=..;f=..;value=..)".
     * Voltages, margin, score, f and value have exactly 3 decimals.
     */
    public static String mathOrigin(Move m) {
        StringBuilder b = new StringBuilder("math_origin=Decision(");
        b.append("t=").append(m.t).append(";lane=").append(m.lane).append(";who=").append(m.who);
        if (KIND_MARGIN.equals(m.kind)) {
            b.append(";V=").append(fixed3(m.vMilli)).append(";th=").append(fixed3(m.thMilli))
                    .append(";margin=").append(fixed3(m.dMilli));
        } else {
            b.append(";dt=").append(num(m.dt)).append(";score=").append(fixed3(m.dMilli));
        }
        b.append(";chain=").append(m.chain).append(";f=").append(fixed3(m.fTenths * 100L))
                .append(";value=").append(fixed3(m.valueMilli)).append(')');
        return b.toString();
    }

    /** Canonical hash preimage: every stored field, '|' separated, then the math_origin segment. */
    public static String preimage(Move m, String prev) {
        return "rhythm-move/v1|prev=" + prev + "|i=" + m.i + "|t=" + m.t + "|lane=" + m.lane
                + "|delta=" + num(m.delta) + "|who=" + m.who + "|press=" + num(m.press) + "|dt=" + num(m.dt)
                + "|judge=" + m.judge + "|fired=" + (m.fired == NA ? "na" : m.fired == 1 ? "yes" : "no")
                + "|lat=" + num(m.lat) + "|" + m.mathOrigin;
    }

    /** JSON object; absent values are null; V / th / margin / score / f / value as 3-decimal numbers. */
    public String toJson() {
        StringBuilder b = new StringBuilder("{");
        b.append("\"i\":").append(i).append(",\"t\":").append(t).append(",\"lane\":").append(lane)
                .append(",\"key\":\"").append(key()).append('"')
                .append(",\"delta\":").append(json(delta)).append(",\"who\":\"").append(who).append('"')
                .append(",\"press\":").append(json(press)).append(",\"dt\":").append(json(dt))
                .append(",\"judge\":\"").append(judge).append('"')
                .append(",\"V\":").append(jsonFixed(vMilli)).append(",\"th\":").append(jsonFixed(thMilli))
                .append(",\"margin\":").append(KIND_MARGIN.equals(kind) ? fixed3(dMilli) : "null")
                .append(",\"fired\":").append(fired == NA ? "null" : fired == 1 ? "true" : "false")
                .append(",\"lat\":").append(json(lat))
                .append(",\"kind\":\"").append(kind).append('"')
                .append(",\"d\":").append(fixed3(dMilli))
                .append(",\"chain\":").append(chain).append(",\"f\":").append(fixed3(fTenths * 100L))
                .append(",\"value\":").append(fixed3(valueMilli))
                .append(",\"math_origin\":\"").append(esc(mathOrigin)).append('"')
                .append(",\"prev\":\"").append(prev).append('"')
                .append(",\"hash\":\"").append(hash).append('"').append('}');
        return b.toString();
    }

    private static String json(long v) {
        return v == NA ? "null" : String.valueOf(v);
    }

    private static String jsonFixed(long v) {
        return v == NA ? "null" : fixed3(v);
    }

    private static String esc(String s) {
        StringBuilder b = new StringBuilder();
        for (int k = 0; k < s.length(); k++) {
            char c = s.charAt(k);
            if (c == '"' || c == '\\') {
                b.append('\\');
            }
            b.append(c);
        }
        return b.toString();
    }

    /** One console line (?debug=notes). */
    public String logLine() {
        return "[moves] #" + i + " t=" + t + " " + key() + " delta=" + num(delta) + " " + who
                + " press=" + num(press) + " dt=" + signed(dt) + " " + judge
                + (vMilli == NA ? "" : " V=" + fixed3(vMilli) + " th=" + fixed3(thMilli))
                + (fired == NA ? "" : fired == 1 ? " fired lat=" + num(lat) : " not-fired")
                + " " + kind + "=" + fixed3(dMilli) + " chain=" + chain + " value=" + fixed3(valueMilli)
                + " hash=" + hash.substring(0, 8);
    }

    /** Compact on-stage row (<= 52 chars, fits the 390 px iPhone stage at 9 px monospace). */
    public String stageLine() {
        String j = judge.substring(0, Math.min(2, judge.length()));
        String w = "fly".equals(who) ? "fly" : "you".equals(who) ? "you" : " - ";
        return pad(String.valueOf(i), 3) + " " + pad(String.valueOf(t), 6) + " " + key() + " " + w + " "
                + pad(dt == NA ? "-" : signed(dt), 4) + " " + j + " " + pad(fixed3(dMilli), 7) + " "
                + pad(String.valueOf(chain), 2) + " " + pad(fixed3(valueMilli), 7) + " " + hash.substring(0, 8);
    }

    public static String stageHeader() {
        return "  #      t L who   dt J       d ch   value hash";
    }

    private static String signed(long v) {
        return v == NA ? "na" : v > 0 ? "+" + v : String.valueOf(v);
    }

    private static String pad(String s, int w) {
        StringBuilder b = new StringBuilder();
        for (int k = s.length(); k < w; k++) {
            b.append(' ');
        }
        return b.append(s).toString();
    }
}
