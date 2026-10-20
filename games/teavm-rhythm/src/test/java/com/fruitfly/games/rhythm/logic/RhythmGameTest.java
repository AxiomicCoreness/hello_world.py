package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.junit.jupiter.api.Test;

class RhythmGameTest {

    /** Chart of n notes, all in lane 0, every 1000 ms starting at 1000. */
    private static RhythmGame lane0(int n) {
        return new RhythmGame(TestCharts.of(n, 0, 1000, 1000));
    }

    @Test
    void perfectHitScoresAndStartsCombo() {
        RhythmGame g = lane0(3);
        assertEquals(Judgement.PERFECT, g.press(0, 1010));
        assertEquals(300, g.score());
        assertEquals(1, g.combo());
        assertEquals(1, g.perfectCount());
    }

    @Test
    void greatAndGoodByOffset() {
        RhythmGame g = lane0(3);
        assertEquals(Judgement.GREAT, g.press(0, 1000 - 80));
        assertEquals(Judgement.GOOD, g.press(0, 2000 + 140));
        assertEquals(300, g.score());
    }

    @Test
    void wrongLaneOrTooEarlyPressIsIgnored() {
        RhythmGame g = lane0(2);
        assertNull(g.press(1, 1000));
        assertNull(g.press(0, 1000 - 151));
        assertNull(g.press(-1, 1000));
        assertNull(g.press(4, 1000));
        assertEquals(0, g.score());
        assertEquals(0, g.combo());
        assertEquals(0, g.missCount());
    }

    @Test
    void eachNoteCanOnlyBeHitOnce() {
        RhythmGame g = lane0(2);
        assertEquals(Judgement.PERFECT, g.press(0, 1000));
        assertNull(g.press(0, 1001));
        assertEquals(1, g.combo());
    }

    @Test
    void lateNoteBecomesMissAndResetsCombo() {
        RhythmGame g = lane0(4);
        g.press(0, 1000);
        g.press(0, 2000);
        assertEquals(2, g.combo());
        g.update(3150); // exactly at the edge: still hittable
        assertEquals(0, g.missCount());
        g.update(3151);
        assertEquals(1, g.missCount());
        assertEquals(0, g.combo());
        assertEquals(2, g.maxCombo());
        assertEquals(Judgement.MISS, g.lastJudgement());
        assertNull(g.press(0, 3151)); // the missed note can no longer be hit
    }

    @Test
    void pressAlsoResolvesOverdueMissesFirst() {
        RhythmGame g = lane0(3);
        g.press(0, 1000);
        // skip note at 2000, press for note at 3000
        assertEquals(Judgement.PERFECT, g.press(0, 3000));
        assertEquals(1, g.missCount());
        assertEquals(1, g.combo()); // reset by miss, then +1
    }

    @Test
    void multiplierStepsEveryTenAndCapsAtFour() {
        assertEquals(1, RhythmGame.multiplierFor(0));
        assertEquals(1, RhythmGame.multiplierFor(9));
        assertEquals(2, RhythmGame.multiplierFor(10));
        assertEquals(3, RhythmGame.multiplierFor(20));
        assertEquals(4, RhythmGame.multiplierFor(30));
        assertEquals(4, RhythmGame.multiplierFor(1000));
    }

    @Test
    void allPerfectScoreUsesComboBeforeHit() {
        RhythmGame g = lane0(35);
        for (int i = 0; i < 35; i++) {
            assertEquals(Judgement.PERFECT, g.press(0, 1000 + 1000L * i));
        }
        // combos 0-9 x1, 10-19 x2, 20-29 x3, 30-34 x4
        long expected = 300L * (10 * 1 + 10 * 2 + 10 * 3 + 5 * 4);
        assertEquals(expected, g.score());
        assertEquals(35, g.maxCombo());
        assertTrue(g.isFinished());
        assertEquals(1.0, g.accuracy(), 1e-12);
    }

    @Test
    void finishedAfterAllNotesResolvedAndAccuracy() {
        RhythmGame g = lane0(2);
        assertFalse(g.isFinished());
        assertEquals(1.0, g.accuracy());
        g.press(0, 1000);
        g.update(10_000);
        assertTrue(g.isFinished());
        assertEquals(0.5, g.accuracy(), 1e-12);
    }

    @Test
    void earliestNoteInLaneIsTakenWhenTwoAreInWindow() {
        RhythmGame g = new RhythmGame(TestCharts.of(2, 0, 1000, 100));
        assertEquals(Judgement.GREAT, g.press(0, 1080)); // note @1000 offset 80, not @1100
        List<Note> n = g.chart().notes();
        assertEquals(Judgement.GREAT, n.get(0).result());
        assertFalse(n.get(1).isResolved());
    }

    @Test
    void laneKeyMapping() {
        assertEquals(0, RhythmGame.laneForKey("d"));
        assertEquals(1, RhythmGame.laneForKey("F"));
        assertEquals(2, RhythmGame.laneForKey("KeyJ"));
        assertEquals(3, RhythmGame.laneForKey("k"));
        assertEquals(-1, RhythmGame.laneForKey("a"));
        assertEquals(-1, RhythmGame.laneForKey("Enter"));
        assertEquals(-1, RhythmGame.laneForKey(null));
    }

    /** Full seeded run: an autoplayer hitting every note on time is deterministic. */
    @Test
    void seededAutoplayIsDeterministic() {
        long[] scores = new long[2];
        for (int r = 0; r < 2; r++) {
            RhythmGame g = new RhythmGame(NoteChart.generate(2026, 64, 120, 2000));
            int i = 0;
            for (Note n : g.chart().notes()) {
                long jitter = (i++ % 3) * 60L; // 0, 60, 120 ms late: PERFECT, GREAT, GOOD
                g.press(n.lane(), n.timeMs() + jitter);
            }
            g.update(Long.MAX_VALUE / 2);
            assertTrue(g.isFinished());
            assertEquals(0, g.missCount());
            assertEquals(64, g.maxCombo());
            scores[r] = g.score();
        }
        assertEquals(scores[0], scores[1]);
    }
}
