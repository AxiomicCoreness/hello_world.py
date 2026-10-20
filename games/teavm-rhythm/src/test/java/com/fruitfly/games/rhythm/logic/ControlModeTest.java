package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.HashSet;
import java.util.Set;
import org.junit.jupiter.api.Test;

/** Mode cycling shared by key C and the AUTOPLAY button, key B's toggle, the labels and the button's placement. */
class ControlModeTest {
    private static final StageLayout[] LAYOUTS = {StageLayout.of(390, 844), StageLayout.of(510, 960), StageLayout.of(400, 600)};

    @Test
    void cycleVisitsEveryModeInOrderAndWraps() {
        int[] expected = {ControlMode.LIF, ControlMode.CONNECTOME, ControlMode.ASSIST_LIF,
            ControlMode.ASSIST_CONNECTOME, ControlMode.OFF};
        int m = ControlMode.OFF;
        for (int e : expected) {
            m = ControlMode.cycle(m, false);
            assertEquals(e, m);
        }
    }

    @Test
    void nothingChangesWhileASongRuns() {
        for (int m = 0; m < ControlMode.COUNT; m++) {
            assertEquals(m, ControlMode.cycle(m, true));
            assertEquals(m, ControlMode.toggleLif(m, true));
        }
    }

    @Test
    void keyBTogglesLifAndAnyOtherModeGoesToLif() {
        assertEquals(ControlMode.LIF, ControlMode.toggleLif(ControlMode.OFF, false));
        assertEquals(ControlMode.OFF, ControlMode.toggleLif(ControlMode.LIF, false));
        assertEquals(ControlMode.LIF, ControlMode.toggleLif(ControlMode.CONNECTOME, false));
        assertEquals(ControlMode.LIF, ControlMode.toggleLif(ControlMode.ASSIST_CONNECTOME, false));
    }

    @Test
    void labelsAreDistinctAndNameTheFly() {
        assertEquals("AUTOPLAY: OFF", ControlMode.buttonLabel(ControlMode.OFF));
        assertEquals("AUTOPLAY: LIF FLY", ControlMode.buttonLabel(ControlMode.LIF));
        assertEquals("AUTOPLAY: CONNECTOME FLY", ControlMode.buttonLabel(ControlMode.CONNECTOME));
        assertEquals("AUTOPLAY: ASSIST \u00b7 LIF FLY", ControlMode.buttonLabel(ControlMode.ASSIST_LIF));
        assertEquals("AUTOPLAY: ASSIST \u00b7 CONNECTOME FLY", ControlMode.buttonLabel(ControlMode.ASSIST_CONNECTOME));
        Set<String> b = new HashSet<>();
        Set<String> h = new HashSet<>();
        for (int m = 0; m < ControlMode.COUNT; m++) {
            assertTrue(ControlMode.buttonLabel(m).startsWith("AUTOPLAY: "));
            b.add(ControlMode.buttonLabel(m));
            h.add(ControlMode.hudText(m));
        }
        assertEquals(ControlMode.COUNT, b.size());
        assertEquals(ControlMode.COUNT, h.size());
        assertEquals("autoplay off", ControlMode.hudText(ControlMode.OFF));
        assertEquals("assist ON (connectome fly)", ControlMode.hudText(ControlMode.ASSIST_CONNECTOME));
        assertEquals(33, ControlMode.longestButtonLabel());
    }

    @Test
    void modeKindsAndRangeCheck() {
        assertTrue(ControlMode.isFullAutoplay(ControlMode.LIF) && ControlMode.isFullAutoplay(ControlMode.CONNECTOME));
        assertFalse(ControlMode.isFullAutoplay(ControlMode.OFF) || ControlMode.isFullAutoplay(ControlMode.ASSIST_LIF));
        assertTrue(ControlMode.isAssist(ControlMode.ASSIST_LIF) && ControlMode.isAssist(ControlMode.ASSIST_CONNECTOME));
        assertFalse(ControlMode.isAssist(ControlMode.OFF) || ControlMode.isAssist(ControlMode.CONNECTOME));
        assertThrows(IllegalArgumentException.class, () -> ControlMode.cycle(5, false));
        assertThrows(IllegalArgumentException.class, () -> ControlMode.buttonLabel(-1));
    }

    @Test
    void buttonIsATapTargetThatFitsItsLongestLabel() {
        for (StageLayout l : LAYOUTS) {
            double[] r = l.autoplayButton();
            assertTrue(r[2] >= StageLayout.BUTTON_MIN_TAP && r[3] >= StageLayout.BUTTON_MIN_TAP, "44 CSS px tap target");
            assertTrue(r[0] >= 0 && r[0] + r[2] <= l.width, "inside the stage horizontally");
            assertEquals(l.width / 2.0, r[0] + r[2] / 2.0, 0.5, "centred (whole CSS px)");
            double text = ControlMode.longestButtonLabel() * 0.62 * StageLayout.BUTTON_FONT_PX;
            assertTrue(text + 16 <= r[2], "longest label fits inside the padding");
        }
    }

    @Test
    void buttonClearsHudTitleTextLanesKeysAndCaption() {
        for (StageLayout l : LAYOUTS) {
            double[] r = l.autoplayButton();
            double top = r[1];
            double bottom = r[1] + r[3];
            assertTrue(top >= l.hudBottom(), "below the tallest corner HUD (5 lines)");
            assertTrue(bottom < l.centerTextTop(), "above the centre text (title prompt / banner)");
            // centre text: <= 5 lines of ~24 px, still above the horizon where the lanes start
            assertTrue(l.centerTextTop() + 5 * 24 < l.horizonY, "title text ends above the horizon");
            assertTrue(bottom < l.horizonY, "above the horizon and every note lane");
            assertTrue(bottom < l.hitY && bottom < l.captionY() - 20, "far from the hit line, key labels and caption");
            // note blocks are drawn below the horizon only (they spawn at the vanishing point)
            Scene3D cam = l.camera();
            for (int lane = 0; lane < 4; lane++) {
                double[] far = cam.project(NoteBlocks.LANE_X[lane], NoteBlocks.Y, -1e9);
                assertTrue(far[1] > bottom, "lane " + lane + " vanishing point below the button");
            }
        }
    }
}
