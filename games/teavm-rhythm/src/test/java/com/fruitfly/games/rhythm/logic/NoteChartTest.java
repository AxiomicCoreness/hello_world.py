package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;

class NoteChartTest {

    private static List<String> sig(NoteChart c) {
        List<String> out = new ArrayList<>();
        for (Note n : c.notes()) {
            out.add(n.lane() + "@" + n.timeMs());
        }
        return out;
    }

    @Test
    void sameSeedSameChart() {
        assertEquals(sig(NoteChart.generate(42, 200, 120, 2000)),
                sig(NoteChart.generate(42, 200, 120, 2000)));
    }

    @Test
    void differentSeedDifferentChart() {
        assertNotEquals(sig(NoteChart.generate(1, 64, 120, 2000)),
                sig(NoteChart.generate(2, 64, 120, 2000)));
    }

    /** Golden prefix: pins the LCG so a JVM/TeaVM or refactor drift shows up. */
    @Test
    void goldenPrefixForSeed2026() {
        List<String> s = sig(NoteChart.generate(2026, 8, 120, 2000));
        assertEquals(List.of("2@2000", "2@2500", "0@3000", "0@3250", "2@3500", "0@3750", "3@4000", "2@4250"), s);
    }

    @Test
    void timesStartAtLeadInAndStrictlyIncreaseByHalfOrFullBeat() {
        NoteChart c = NoteChart.generate(7, 500, 120, 2000);
        assertEquals(2000, c.notes().get(0).timeMs());
        for (int i = 1; i < c.notes().size(); i++) {
            long d = c.notes().get(i).timeMs() - c.notes().get(i - 1).timeMs();
            assertTrue(d == 250 || d == 500, "step " + d);
        }
        assertEquals(c.notes().get(499).timeMs(), c.lastNoteMs());
    }

    @Test
    void lanesInRangeAllUsedAndNoLaneMoreThanTwiceInARow() {
        NoteChart c = NoteChart.generate(99, 1000, 140, 0);
        boolean[] seen = new boolean[RhythmGame.LANES];
        int run = 0;
        int prev = -1;
        for (Note n : c.notes()) {
            assertTrue(n.lane() >= 0 && n.lane() < RhythmGame.LANES);
            seen[n.lane()] = true;
            run = n.lane() == prev ? run + 1 : 1;
            prev = n.lane();
            assertTrue(run <= 2, "lane run of " + run);
        }
        for (boolean b : seen) {
            assertTrue(b);
        }
    }

    @Test
    void freshCopyIsUnresolvedAndIdentical() {
        NoteChart c = NoteChart.generate(5, 10, 120, 1000);
        RhythmGame g = new RhythmGame(c);
        g.update(1_000_000);
        assertTrue(g.isFinished());
        NoteChart f = c.fresh();
        assertEquals(sig(c), sig(f));
        for (Note n : f.notes()) {
            assertFalse(n.isResolved());
        }
    }

    @Test
    void rejectsBadArguments() {
        assertThrows(IllegalArgumentException.class, () -> NoteChart.generate(1, -1, 120, 0));
        assertThrows(IllegalArgumentException.class, () -> NoteChart.generate(1, 1, 0, 0));
        assertThrows(IllegalArgumentException.class, () -> NoteChart.generate(1, 1, 120, -5));
        assertThrows(IllegalArgumentException.class, () -> new Note(4, 0));
        assertThrows(IllegalArgumentException.class, () -> new Note(0, -1));
        assertEquals(0, NoteChart.generate(1, 0, 120, 0).lastNoteMs());
    }
}
