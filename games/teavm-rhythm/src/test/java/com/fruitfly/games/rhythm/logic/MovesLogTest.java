package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.security.MessageDigest;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;

/** The moves list: rows, decision values, chain, math_origin and the hash chain. */
class MovesLogTest {
    static final Circuit TOY = FlyPlay.TOY;

    /** Plays a chart with the connectome fly (or LIF, or nobody) at 16 ms frames, as the page does, and returns the log. */
    static MovesLog play(NoteChart chart, int mode) {
        RhythmGame g = new RhythmGame(chart.fresh());
        LifAutoplayer lif = new LifAutoplayer(g);
        ConnectomeAutoplayer con = new ConnectomeAutoplayer(g, TOY);
        CueProbe probe = mode == ControlMode.LIF ? lif.probe() : mode == ControlMode.CONNECTOME ? con.probe() : null;
        MovesLog log = new MovesLog(g, mode, probe);
        long end = g.chart().lastNoteMs() + 1000;
        for (long t = 0; t <= end; t += 16) {
            if (mode == ControlMode.LIF) {
                lif.advanceTo(t);
            } else if (mode == ControlMode.CONNECTOME) {
                con.advanceTo(t);
            }
            g.update(t);
            log.update(t);
        }
        return log;
    }

    static NoteChart bembe90() {
        return EuclidSong.chart(EuclidSong.PRESETS[EuclidSong.indexOf("bembe")], 90).chart();
    }

    @Test
    void connectomeFlyOnBembeEveryRowFiredWithNonNegativeMargin() {
        MovesLog log = play(bembe90(), ControlMode.CONNECTOME);
        List<Move> rows = log.recent();
        assertEquals(56, log.size());
        assertEquals(56, rows.size());
        long prevT = -1;
        int[] chain = new int[4];
        for (Move m : rows) {
            assertEquals("fly", m.who);
            assertEquals("PERFECT", m.judge);
            assertEquals(1, m.fired, "row " + m.i);
            assertEquals(Move.KIND_MARGIN, m.kind);
            assertTrue(m.dMilli >= 0, "fired -> margin >= 0, row " + m.i + " " + m.dMilli);
            assertEquals(m.vMilli - MovesLog.TH_MILLI, m.dMilli);
            assertEquals(-45000, m.thMilli);
            assertEquals(m.press - m.t, m.dt);
            assertEquals(ConnectomeAutoplayer.measureLatencyMs(TOY, m.lane), m.lat, "cue-to-press latency");
            assertEquals(prevT < 0 ? Move.NA : m.t - prevT, m.delta);
            prevT = m.t;
            chain[m.lane]++;
            assertEquals(chain[m.lane], m.chain);
            assertEquals(m.i % 4, m.lane, "single preset spread over the lanes");
        }
        assertEquals(20, log.first20().size());
        assertEquals(-1, log.verifyKept());
    }

    @Test
    void unfiredCuesAreMissRowsWithNegativeMargin() {
        // Two D notes 3 ms apart: the second cue arrives while laneN.out is still serving the first,
        // so it never gets its own spike -> MISS, margin < 0, chain reset.
        List<Note> ns = new ArrayList<>();
        ns.add(new Note(0, 1000));
        ns.add(new Note(1, 1000));
        ns.add(new Note(0, 1003));
        ns.add(new Note(0, 1600));
        MovesLog log = play(NoteChart.fromNotes(ns), ControlMode.CONNECTOME);
        List<Move> r = log.recent();
        assertEquals(4, r.size());
        Move miss = r.get(2);
        assertEquals(0, miss.fired);
        assertEquals("MISS", miss.judge);
        assertEquals("none", miss.who);
        assertTrue(miss.dMilli < 0, "unfired: V_peak below threshold " + miss.dMilli);
        assertEquals(0, miss.chain);
        assertEquals(miss.dMilli, miss.valueMilli, "f(0) = 1");
        assertEquals(1, r.get(3).chain, "D chain restarts after the miss");
        // over bembe and this chart: fired <=> hit, unfired <=> MISS
        for (MovesLog l : new MovesLog[] {log, play(bembe90(), ControlMode.CONNECTOME), play(bembe90(), ControlMode.LIF)}) {
            for (Move m : l.recent()) {
                assertEquals(m.fired == 1, !"MISS".equals(m.judge), "row " + m.i + " " + m.logLine());
                if (m.fired == 1) {
                    assertTrue(m.dMilli >= 0, m.logLine());
                }
            }
        }
    }

    @Test
    void chainResetsOnMissForHumanTimingRows() {
        NoteChart c = TestCharts.of(5, 2, 1000, 500); // J at 1000, 1500, 2000, 2500, 3000
        RhythmGame g = new RhythmGame(c);
        MovesLog log = new MovesLog(g, ControlMode.OFF, null);
        long[] press = {1000 - 12, 1500 + 60, -1, 2500 + 149, 3000};
        for (long t = 0; t <= 4000; t += 1) {
            for (int k = 0; k < press.length; k++) {
                if (press[k] == t) {
                    g.press(2, t);
                }
            }
            g.update(t);
            log.update(t);
        }
        List<Move> r = log.recent();
        int[] chains = {1, 2, 0, 1, 2};
        long[] scores = {920, 600, 0, 7, 1000}; // round(1000 (150 - |dt|) / 150)
        for (int k = 0; k < 5; k++) {
            Move m = r.get(k);
            assertEquals(chains[k], m.chain, "row " + k);
            assertEquals(Move.KIND_TIMING, m.kind);
            assertEquals(scores[k], m.dMilli, "row " + k);
            assertEquals(Move.value(scores[k], 10 + chains[k]), m.valueMilli);
            assertEquals(Move.NA, m.fired);
            assertEquals(k == 2 ? "none" : "you", m.who);
        }
        assertEquals("MISS", r.get(2).judge);
        assertEquals(1196, Move.value(920, 13), "0.920 x 1.3");
        assertEquals(-7700, Move.value(-7000, 11), "half away from zero, negative too");
        assertEquals(-5, Move.value(-5, 10));
        assertEquals(20, Move.chainFactorTenths(42), "f capped at 2.0");
    }

    @Test
    void mathOriginIsRecomputableFromTheFields() {
        for (MovesLog log : new MovesLog[] {play(bembe90(), ControlMode.CONNECTOME), play(bembe90(), ControlMode.OFF)}) {
            for (Move m : log.recent()) {
                String expect;
                if (Move.KIND_MARGIN.equals(m.kind)) {
                    expect = String.format(java.util.Locale.ROOT, "math_origin=Decision(t=%d;lane=%d;who=%s;V=%.3f;th=%.3f;margin=%.3f;chain=%d;f=%.3f;value=%.3f)",
                        m.t, m.lane, m.who, m.vMilli / 1000.0, m.thMilli / 1000.0, (m.vMilli - m.thMilli) / 1000.0, m.chain,
                        1 + Math.min(m.chain, 10) / 10.0, Math.round((m.vMilli - m.thMilli) * (1 + Math.min(m.chain, 10) / 10.0)) / 1000.0);
                } else {
                    expect = String.format(java.util.Locale.ROOT, "math_origin=Decision(t=%d;lane=%d;who=%s;dt=%s;score=%.3f;chain=%d;f=%.3f;value=%.3f)",
                        m.t, m.lane, m.who, m.dt == Move.NA ? "na" : String.valueOf(m.dt), Move.timingScoreMilli(m.dt) / 1000.0, m.chain,
                        1 + Math.min(m.chain, 10) / 10.0, Move.value(Move.timingScoreMilli(m.dt), Move.chainFactorTenths(m.chain)) / 1000.0);
                }
                assertEquals(expect, m.mathOrigin);
                assertEquals(expect, Move.mathOrigin(m));
            }
        }
        assertEquals("-45.000", Move.fixed3(-45000));
        assertEquals("-0.005", Move.fixed3(-5));
        assertEquals("0.388", Move.fixed3(388));
        assertEquals("12.040", Move.fixed3(12040));
    }

    @Test
    void hashChainVerifiesAndDetectsTampering() throws Exception {
        MovesLog log = play(bembe90(), ControlMode.CONNECTOME);
        List<Move> r = log.recent();
        assertEquals(MovesLog.GENESIS, r.get(0).prev);
        assertEquals(64, MovesLog.GENESIS.length());
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        for (int k = 0; k < r.size(); k++) {
            Move m = r.get(k);
            if (k > 0) {
                assertEquals(r.get(k - 1).hash, m.prev);
            }
            String pre = Move.preimage(m, m.prev);
            assertTrue(pre.endsWith("|" + m.mathOrigin) && pre.startsWith("rhythm-move/v1|prev=" + m.prev + "|i=" + m.i + "|"));
            assertEquals(Sha256Test.hex(md.digest(pre.getBytes(StandardCharsets.UTF_8))), m.hash, "JDK SHA-256 agrees, row " + k);
        }
        assertEquals(log.lastHash(), r.get(r.size() - 1).hash);
        assertEquals(-1, MovesLog.verify(r));
        // tamper: a field (hash not updated), a derived string, a hash, and a dropped row
        List<Move> t1 = new ArrayList<>(r);
        Move m5 = r.get(5);
        t1.set(5, new Move(m5, "MISS", m5.mathOrigin, m5.prev, m5.hash));
        assertEquals(5, MovesLog.verify(t1));
        List<Move> t2 = new ArrayList<>(r);
        Move m7 = r.get(7);
        String forged = m7.mathOrigin.replace("value=", "value=9");
        t2.set(7, new Move(m7, m7.judge, forged, m7.prev, Sha256.hex(Move.preimage(new Move(m7, m7.judge, forged, m7.prev, m7.hash), m7.prev))));
        assertEquals(7, MovesLog.verify(t2), "math_origin not re-derivable from the fields (even with a matching hash)");
        List<Move> t3 = new ArrayList<>(r);
        Move m9 = r.get(9);
        t3.set(9, new Move(m9, m9.judge, m9.mathOrigin, m9.prev, "f" + m9.hash.substring(1)));
        assertEquals(m9.hash.charAt(0) == 'f' ? 10 : 9, MovesLog.verify(t3));
        List<Move> t4 = new ArrayList<>(r);
        t4.remove(12);
        assertEquals(13, MovesLog.verify(t4), "a dropped row breaks the next link");
        // a mid-song slice (ring) verifies on its own
        assertEquals(-1, MovesLog.verify(r.subList(30, 56)));
    }

    @Test
    void ringKeepsTheLast64AndTheFirst20() {
        NoteChart c = EuclidSong.chart(EuclidSong.PRESETS[0], 140).chart(); // layered: 19 x 8 = 152 notes
        MovesLog log = play(c, ControlMode.CONNECTOME);
        assertEquals(152, log.size());
        List<Move> ring = log.recent();
        assertEquals(64, ring.size());
        assertEquals(152 - 64, ring.get(0).i);
        assertEquals(151, ring.get(63).i);
        List<Move> f = log.first20();
        assertEquals(20, f.size());
        assertEquals(19, f.get(19).i);
        assertEquals(-1, log.verifyKept());
        assertEquals(8, log.tail(8).size());
        assertEquals(151, log.tail(8).get(7).i);
        String json = MovesLog.toJson(log.tail(1));
        assertTrue(json.startsWith("[{\"i\":151,") && json.contains("\"hash\":\"" + ring.get(63).hash + "\""), json);
        assertFalse(json.contains("NaN") || json.contains("Infinity"));
    }

    @Test
    void rowsWaitUntilTheCueWindowHasSettled() {
        NoteChart c = bembe90();
        RhythmGame g = new RhythmGame(c.fresh());
        ConnectomeAutoplayer con = new ConnectomeAutoplayer(g, TOY);
        MovesLog log = new MovesLog(g, ControlMode.CONNECTOME, con.probe());
        for (long t = 0; t <= 2000 + MovesLog.SETTLE_MS - 16; t += 16) {
            con.advanceTo(t);
            g.update(t);
            log.update(t);
        }
        assertEquals(0, log.size(), "note at 2000 judged, but not settled yet");
        con.advanceTo(2400);
        g.update(2400);
        assertEquals(1, log.update(2400).size());
    }

    @Test
    void stageLinesFitTheIphoneStage() {
        for (Move m : play(EuclidSong.chart(EuclidSong.PRESETS[0], 140).chart(), ControlMode.CONNECTOME).recent()) {
            assertTrue(m.stageLine().length() <= 52, m.stageLine());
        }
        assertTrue(Move.stageHeader().length() <= 52);
    }
}
