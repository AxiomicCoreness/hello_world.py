package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/** Regression: the AUTOPLAY label and the HUD come from the same mode, and "blocks cut" moves with the hit count. */
class HudSyncTest {
    private static final String[] SEQUENCE = {
        "AUTOPLAY: LIF FLY", "AUTOPLAY: CONNECTOME FLY", "AUTOPLAY: ASSIST \u00b7 LIF FLY",
        "AUTOPLAY: ASSIST \u00b7 CONNECTOME FLY", "AUTOPLAY: OFF",
    };
    private static final String[] HUD = {
        "LIF autoplay ON", "connectome autoplay ON", "assist ON (LIF fly)", "assist ON (connectome fly)", "autoplay off",
    };

    @Test
    void labelAfterEachOfNClicksIsTheCycleSequence() {
        int mode = ControlMode.OFF;
        for (int click = 1; click <= 12; click++) {
            mode = ControlMode.cycle(mode, false);
            assertEquals(SEQUENCE[(click - 1) % 5], ControlMode.buttonLabel(mode, false), "after click " + click);
            assertEquals(HUD[(click - 1) % 5], ControlMode.hudText(mode), "HUD after click " + click);
        }
    }

    @Test
    void labelAndHudAgreeAfterTheSongStarts() {
        for (int clicks = 0; clicks < 10; clicks++) {
            int mode = ControlMode.OFF;
            for (int k = 0; k < clicks; k++) {
                mode = ControlMode.cycle(mode, false);
            }
            String idle = ControlMode.buttonLabel(mode, false);
            // Space starts the song: the mode is unchanged, only the label gains the lock.
            assertEquals(InputRouter.START, InputRouter.key(" ", "Space", false, false));
            String locked = ControlMode.buttonLabel(mode, true);
            assertEquals(idle.substring("AUTOPLAY: ".length()), locked.substring("LOCKED: ".length()), clicks + " clicks");
            assertEquals(clicks == 0 ? "autoplay off" : HUD[(clicks - 1) % 5], ControlMode.hudText(mode));
        }
    }

    @Test
    void blocksCutMovesOnThePressLikeTheHitCount() {
        RhythmGame g = new RhythmGame(TestCharts.of(2, 0, 1000, 300));
        Note first = g.chart().notes().get(0);
        Note second = g.chart().notes().get(1);
        g.press(0, 1000);
        assertEquals(1, NoteBlocks.hitCount(g.chart(), 1000), "counted at the press");
        assertEquals(0, NoteBlocks.cutCount(g.chart(), 1000), "split animation not yet");
        g.press(0, 1300);
        assertEquals(2, g.combo());
        assertEquals(2, NoteBlocks.hitCount(g.chart(), 1300), "combo 2 -> blocks cut 2 on the same press");
        assertEquals(1, NoteBlocks.cutCount(g.chart(), 1300), "the old counter lagged here (the reported 2 vs 1)");
        assertEquals(2, NoteBlocks.cutCount(g.chart(), second.judgedAtMs() + SaberRig.CONTACT_MS));
        assertTrue(first.judgedAtMs() <= second.judgedAtMs());
    }

    @Test
    void blocksCutEqualsHitsOnEveryFrameOfAFlyPlayedSong() {
        for (int mode : new int[] {ControlMode.LIF, ControlMode.CONNECTOME}) {
            RhythmGame g = new RhythmGame(EuclidSong.chart(EuclidSong.PRESETS[EuclidSong.indexOf("bembe")], 90).chart());
            java.util.function.LongConsumer brain = mode == ControlMode.LIF ? new LifAutoplayer(g)::advanceTo
                : new ConnectomeAutoplayer(g, FlyPlay.TOY)::advanceTo;
            long end = g.chart().lastNoteMs() + 1000;
            for (long t = 0; t <= end; t += 16) {
                brain.accept(t);
                g.update(t);
                assertEquals(g.perfectCount() + g.greatCount() + g.goodCount(), NoteBlocks.hitCount(g.chart(), t), "t=" + t);
            }
        }
    }
}
