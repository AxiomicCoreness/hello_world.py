package com.fruitfly.games.rhythm.logic;

import java.lang.reflect.Constructor;
import java.util.ArrayList;
import java.util.List;

/** Hand-built charts for tests (same package, so it can use the private constructor via reflection). */
final class TestCharts {
    private TestCharts() {
    }

    static NoteChart of(int n, int lane, long startMs, long stepMs) {
        List<Note> notes = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            notes.add(new Note(lane, startMs + stepMs * i));
        }
        try {
            Constructor<NoteChart> c = NoteChart.class.getDeclaredConstructor(long.class, List.class);
            c.setAccessible(true);
            return c.newInstance(-1L, notes);
        } catch (ReflectiveOperationException e) {
            throw new AssertionError(e);
        }
    }
}
