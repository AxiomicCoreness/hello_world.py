package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;

import java.util.List;
import java.util.function.LongPredicate;
import org.junit.jupiter.api.Test;

class AssistArbiterTest {
    private static final Circuit TOY = ConnectomeXml.parse(ToyCircuitXml.XML);

    /** One assisted run. humanOffset(i) = press offset for note i, or Long.MIN_VALUE to skip it. */
    private static final class Run {
        final RhythmGame game;
        final AssistArbiter arb;
        final Object brain;

        Run(NoteChart chart, boolean connectome) {
            game = new RhythmGame(chart);
            arb = new AssistArbiter(game);
            if (connectome) {
                ConnectomeAutoplayer c = new ConnectomeAutoplayer(game, TOY, AssistArbiter.FLY_AIM_MS, arb);
                arb.attachBrain(c::advanceTo);
                brain = c;
            } else {
                LifAutoplayer p = new LifAutoplayer(game, AssistArbiter.FLY_AIM_MS, arb);
                arb.attachBrain(p::advanceTo);
                brain = p;
            }
        }

        void advance(long t) {
            if (brain instanceof LifAutoplayer) {
                ((LifAutoplayer) brain).advanceTo(t);
            } else {
                ((ConnectomeAutoplayer) brain).advanceTo(t);
            }
            game.update(t);
        }

        /** Frame loop at frameMs with human presses at note time + offset for the notes `human` selects. */
        long[] play(long frameMs, LongPredicate human, long offset) {
            List<Note> notes = game.chart().notes();
            long[] pressAt = new long[notes.size()];
            for (int i = 0; i < notes.size(); i++) {
                pressAt[i] = human.test(i) ? notes.get(i).timeMs() + offset : Long.MAX_VALUE;
            }
            long end = game.chart().lastNoteMs() + 1000;
            for (long t = 0; t <= end; t += frameMs) {
                for (int i = 0; i < notes.size(); i++) {
                    if (pressAt[i] <= t) { // key event handled at the frame it lands in, with its own timestamp
                        arb.human(notes.get(i).lane(), pressAt[i]);
                        pressAt[i] = Long.MAX_VALUE;
                    }
                }
                advance(t);
            }
            advance(end);
            return new long[] {game.score(), game.perfectCount(), game.greatCount(), game.goodCount(),
                game.missCount(), arb.humanHits(), arb.flyHits(), arb.flyHeld()};
        }
    }

    private static NoteChart seed() {
        return NoteChart.generate(2026, 64, 120, 2000);
    }

    @Test
    void humanHitsEverything_flyNeverPresses() {
        for (boolean wired : new boolean[] {false, true}) {
            long[] r = new Run(seed(), wired).play(16, i -> true, 0);
            assertEquals(64, r[1], "all PERFECT by the human");
            assertEquals(64, r[5]);
            assertEquals(0, r[6], "fly hits");
            assertEquals(64, r[7], "every fly spike held");
            assertEquals(0, r[4]);
        }
    }

    @Test
    void humanPlaysNothing_flyCoversEveryNote() {
        for (boolean wired : new boolean[] {false, true}) {
            long[] r = new Run(seed(), wired).play(16, i -> false, 0);
            assertEquals(0, r[5]);
            assertEquals(64, r[6], "fly covers all (connectome=" + wired + ")");
            assertEquals(64, r[2], "covers land GREAT (95 ms late)");
            assertEquals(0, r[4], "no misses");
        }
    }

    @Test
    void humanHitsEvenNotes_flyCoversTheRest() {
        for (boolean wired : new boolean[] {false, true}) {
            long[] r = new Run(seed(), wired).play(16, i -> i % 2 == 0, 0);
            assertEquals(32, r[5], "human");
            assertEquals(32, r[6], "fly");
            assertEquals(32, r[1]);
            assertEquals(32, r[2]);
            assertEquals(0, r[4]);
            assertEquals(32, r[7], "fly held for the human's notes");
        }
    }

    @Test
    void humanLateHitBeforeTheFlyStillCountsAsHuman() {
        // Human presses every note 80 ms late (GREAT, still before the fly's 95 ms): all human, none fly.
        long[] r = new Run(seed(), false).play(16, i -> true, 80);
        assertEquals(64, r[5]);
        assertEquals(0, r[6]);
        assertEquals(64, r[2]);
        // 120 ms late: the fly (at 95) gets there first; the human's press then finds nothing: no double judging.
        // (Sparse chart, 500 ms apart, so the late human press can't reach the next note early.)
        Run late = new Run(TestCharts.of(8, 1, 1000, 500), false);
        long[] q = late.play(16, i -> true, 120);
        assertEquals(0, q[5]);
        assertEquals(8, q[6]);
        assertEquals(8, q[1] + q[2] + q[3] + q[4], "each note judged exactly once");
        assertEquals(8, q[2]);
    }

    @Test
    void flyNeverTakesANoteEarlyOrStealsTheNextOne() {
        RhythmGame g = new RhythmGame(TestCharts.of(2, 0, 1000, 120)); // lane 0 at 1000 and 1120
        AssistArbiter a = new AssistArbiter(g);
        a.fly(0, 1050);               // 50 ms late on note 1000: too early to cover
        assertEquals(1, a.flyHeld());
        assertNull(g.chart().notes().get(0).result());
        assertSame(Judgement.PERFECT, a.human(0, 1000 + 20));
        a.fly(0, 1095);               // note 1000 is the human's; 1120 is 25 ms early -> held, not stolen
        assertEquals(2, a.flyHeld());
        assertNull(g.chart().notes().get(1).result());
        a.fly(0, 1120 + 95);          // covers note 1120
        assertEquals(1, a.flyHits());
        assertSame(Judgement.GREAT, g.chart().notes().get(1).result());
        a.fly(0, 1120 + 96);          // already judged -> held
        assertEquals(3, a.flyHeld());
        assertEquals(1, a.humanHits());
    }

    @Test
    void deterministicAcrossRunsAndFrameRates() {
        for (boolean wired : new boolean[] {false, true}) {
            long[] a = new Run(seed(), wired).play(16, i -> i % 3 == 0, 30);
            for (long frame : new long[] {16, 7, 33, 1000}) {
                long[] b = new Run(seed(), wired).play(frame, i -> i % 3 == 0, 30);
                for (int k = 0; k < a.length; k++) {
                    assertEquals(a[k], b[k], "connectome=" + wired + " frame " + frame + " field " + k);
                }
            }
            assertEquals(22, a[5]);
            assertEquals(42, a[6]);
            assertEquals(0, a[4]);
        }
    }
}
