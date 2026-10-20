package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/** Bug fixes: the silent mid-song mode lock, and Space stepping the mode after the AUTOPLAY button was used. */
class InputRouterTest {
    private static final String[][] START_KEYS = {{" ", "Space"}, {"Enter", "Enter"}, {"Spacebar", ""}, {"Enter", "NumpadEnter"}};

    @Test
    void spaceAndEnterOnlyStartASongAndNeverCycleTheMode() {
        for (String[] k : START_KEYS) {
            assertEquals(InputRouter.START, InputRouter.key(k[0], k[1], false, false), k[0]);
            assertEquals(InputRouter.CONSUME, InputRouter.key(k[0], k[1], false, true), k[0]);
            assertEquals(InputRouter.CONSUME, InputRouter.key(k[0], k[1], true, false), "held Space does not restart");
            for (boolean running : new boolean[] {false, true}) {
                for (boolean repeat : new boolean[] {false, true}) {
                    int a = InputRouter.key(k[0], k[1], repeat, running);
                    assertNotEquals(InputRouter.CYCLE_MODE, a);
                    assertNotEquals(InputRouter.TOGGLE_LIF, a);
                }
            }
        }
    }

    @Test
    void keyboardSynthesisedButtonClickIsIgnored() {
        // Space / Enter on a focused <button> fires click with detail 0: must not step the mode.
        assertEquals(InputRouter.NONE, InputRouter.buttonClick(0, false));
        assertEquals(InputRouter.NONE, InputRouter.buttonClick(0, true));
        // Real taps / mouse clicks (detail >= 1) cycle between songs.
        assertEquals(InputRouter.CYCLE_MODE, InputRouter.buttonClick(1, false));
        assertEquals(InputRouter.CYCLE_MODE, InputRouter.buttonClick(2, false));
    }

    @Test
    void spaceAfterTwoButtonTapsStartsWithTheSameMode() {
        int mode = ControlMode.OFF;
        boolean running = false;
        for (int tap = 0; tap < 2; tap++) {
            assertEquals(InputRouter.CYCLE_MODE, InputRouter.buttonClick(1, running));
            mode = ControlMode.cycle(mode, running);
        }
        assertEquals(ControlMode.CONNECTOME, mode);
        // Space keydown, then the click a focused button would synthesise on keyup.
        assertEquals(InputRouter.START, InputRouter.key(" ", "Space", false, running));
        running = true;
        assertEquals(InputRouter.NONE, InputRouter.buttonClick(0, running));
        assertEquals(ControlMode.CONNECTOME, mode);
        assertEquals("LOCKED: CONNECTOME FLY", ControlMode.buttonLabel(mode, running));
    }

    @Test
    void modeKeysAndTapsMidSongReportLockedSoTheHintShows() {
        assertEquals(InputRouter.LOCKED, InputRouter.key("c", "KeyC", false, true));
        assertEquals(InputRouter.LOCKED, InputRouter.key("C", "KeyC", false, true));
        assertEquals(InputRouter.LOCKED, InputRouter.key("b", "KeyB", false, true));
        assertEquals(InputRouter.LOCKED, InputRouter.buttonClick(1, true));
        assertEquals(InputRouter.CYCLE_MODE, InputRouter.key("c", "KeyC", false, false));
        assertEquals(InputRouter.TOGGLE_LIF, InputRouter.key("b", "KeyB", false, false));
        // Layout-independent: physical key C on a non-QWERTY layout.
        assertEquals(InputRouter.CYCLE_MODE, InputRouter.key("\u0441", "KeyC", false, false));
    }

    @Test
    void heldModeKeysStepOnce() {
        assertEquals(InputRouter.NONE, InputRouter.key("c", "KeyC", true, false));
        assertEquals(InputRouter.NONE, InputRouter.key("b", "KeyB", true, false));
        assertEquals(InputRouter.NONE, InputRouter.key("c", "KeyC", true, true));
    }

    @Test
    void otherKeysKeepTheirOldMeaning() {
        assertEquals(InputRouter.NEW_SEED, InputRouter.key("n", "KeyN", false, false));
        assertEquals(InputRouter.NONE, InputRouter.key("r", "KeyR", false, false));
        assertEquals(InputRouter.RESTART, InputRouter.key("r", "KeyR", false, true));
        assertEquals(InputRouter.LANE, InputRouter.key("d", "KeyD", false, true));
        assertEquals(InputRouter.NONE, InputRouter.key("d", "KeyD", true, true));
        assertEquals(InputRouter.NONE, InputRouter.key("d", "KeyD", false, false));
    }

    @Test
    void lockedLabelAndHintAreVisibleAndFitTheButton() {
        for (int m = 0; m < ControlMode.COUNT; m++) {
            String idle = ControlMode.buttonLabel(m, false);
            String locked = ControlMode.buttonLabel(m, true);
            assertEquals(ControlMode.buttonLabel(m), idle);
            assertTrue(locked.startsWith("LOCKED: "), locked);
            assertTrue(locked.length() <= ControlMode.longestButtonLabel(), locked);
            assertEquals(idle.substring("AUTOPLAY: ".length()), locked.substring("LOCKED: ".length()));
        }
        assertTrue(ControlMode.LOCK_HINT.contains("locked during song") && ControlMode.LOCK_HINT.contains("press R"));
        assertTrue(ControlMode.buttonTitle(true).startsWith("Locked"));
        assertTrue(ControlMode.LOCK_HINT_MS >= 1000);
    }
}
