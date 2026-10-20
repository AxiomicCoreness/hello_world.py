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

    @Test
    void songPickerKeysCycleBetweenSongsAndLockDuringOne() {
        assertEquals(InputRouter.CYCLE_RHYTHM, InputRouter.key("e", "KeyE", false, false));
        assertEquals(InputRouter.CYCLE_BPM, InputRouter.key("t", "KeyT", false, false));
        assertEquals(InputRouter.LOCKED, InputRouter.key("e", "KeyE", false, true));
        assertEquals(InputRouter.LOCKED, InputRouter.key("t", "KeyT", false, true));
        assertEquals(InputRouter.NONE, InputRouter.key("e", "KeyE", true, false));
    }

    @Test
    void pickerRowIsATapTargetRowUnderTheAutoplayButton() {
        for (StageLayout l : new StageLayout[] {StageLayout.of(390, 844), StageLayout.of(510, 960), StageLayout.of(400, 600)}) {
            double[] a = l.autoplayButton();
            for (double[][] row : new double[][][] {l.pickerRow(0.7, 0.3), l.pickerRow(0.24, 0.5, 0.26)}) {
                assertEquals(a[0], row[0][0], 1e-9);
                assertEquals(a[0] + a[2], row[row.length - 1][0] + row[row.length - 1][2], 1e-9, "same span as AUTOPLAY");
                for (int i = 0; i < row.length; i++) {
                    assertTrue(row[i][2] >= StageLayout.BUTTON_MIN_TAP && row[i][3] >= StageLayout.BUTTON_MIN_TAP, "44 px tap target");
                    assertTrue(row[i][1] >= a[1] + a[3], "below AUTOPLAY");
                    assertTrue(row[i][1] + row[i][3] < l.centerTextTopBelowPickers(), "above the centre text");
                    if (i > 0) {
                        assertTrue(row[i][0] >= row[i - 1][0] + row[i - 1][2] + StageLayout.PICKER_GAP - 1e-9, "no overlap");
                    }
                }
            }
            assertTrue(l.centerTextTopBelowPickers() < l.horizonY, "centre text starts above the horizon");
            // The longest rhythm label fits the 0.7 share at the picker font.
            int longest = 0;
            for (EuclidSong.Preset p : EuclidSong.PRESETS) {
                longest = Math.max(longest, p.label.length());
            }
            assertTrue(longest * 0.62 * StageLayout.PICKER_FONT_PX + 12 <= l.pickerRow(0.7, 0.3)[0][2], "label fits");
            // Three-button row (source / item / tempo) as on the page: every label fits its button.
            double[][] row3 = l.pickerRow(0.26, 0.48, 0.26);
            for (String[] v : VoiceSong.LINES) {
                longest = Math.max(longest, v[1].length());
            }
            longest = Math.max(longest, SongSource.midiLabel("abcdefghijklmnopqrstuvwxyz.mid").length());
            assertTrue(longest * 0.62 * StageLayout.PICKER_FONT_PX + 12 <= row3[1][2], "item label fits " + row3[1][2]);
            for (int s = 0; s < SongSource.COUNT; s++) {
                assertTrue(SongSource.label(s).length() * 0.62 * StageLayout.PICKER_FONT_PX + 12 <= row3[0][2], "source label fits");
            }
            for (String b : new String[] {"FILE BPM", "140 BPM", "-- BPM"}) {
                assertTrue(b.length() * 0.62 * StageLayout.PICKER_FONT_PX + 12 <= row3[2][2], b + " fits " + row3[2][2]);
            }
        }
    }
}
