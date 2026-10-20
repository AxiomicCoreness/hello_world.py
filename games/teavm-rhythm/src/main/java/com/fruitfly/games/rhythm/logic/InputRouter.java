package com.fruitfly.games.rhythm.logic;

/**
 * Pure routing of keyboard input and on-screen button clicks to game actions,
 * so the browser layer has one place that decides what a key or click does.
 *
 * Rules (tested in InputRouterTest):
 * <ul>
 * <li>Only C / the AUTOPLAY button cycle the mode, only B toggles the LIF
 * fly; auto-repeat of a held C or B is ignored (one press, one step).</li>
 * <li>Space / Enter only ever start a song (between songs); they never cycle
 * the mode, and mid-song they do nothing but are still consumed.</li>
 * <li>Mode changes stay locked during a song; the attempt returns
 * {@link #LOCKED} so the page can show {@link ControlMode#LOCK_HINT}.</li>
 * <li>A button click with {@code detail == 0} is a keyboard-synthesised
 * activation (Space / Enter on a focused button), not a tap or mouse click,
 * and is ignored: Space must start the song, not step the mode.</li>
 * </ul>
 */
public final class InputRouter {
    public static final int NONE = 0;
    public static final int CYCLE_MODE = 1;
    public static final int TOGGLE_LIF = 2;
    /** A mode change was attempted mid-song: show the lock hint. */
    public static final int LOCKED = 3;
    public static final int START = 4;
    public static final int NEW_SEED = 5;
    public static final int RESTART = 6;
    /** A possible lane key during a song (the caller maps it with RhythmGame.laneForKey). */
    public static final int LANE = 7;
    /** Space / Enter mid-song: no action, but preventDefault (no page scroll, no button activation). */
    public static final int CONSUME = 8;

    private InputRouter() {
    }

    public static boolean isStartKey(String key, String code) {
        return " ".equals(key) || "Spacebar".equals(key) || "Enter".equals(key)
                || "Space".equals(code) || "Enter".equals(code) || "NumpadEnter".equals(code);
    }

    private static boolean is(String key, String code, char letter) {
        return (key != null && key.length() == 1 && Character.toLowerCase(key.charAt(0)) == letter)
                || ("Key" + Character.toUpperCase(letter)).equals(code);
    }

    /** What a keydown does. {@code repeat} is KeyboardEvent.repeat. */
    public static int key(String key, String code, boolean repeat, boolean running) {
        if (isStartKey(key, code)) {
            return running || repeat ? CONSUME : START;
        }
        if (is(key, code, 'c') || is(key, code, 'b')) {
            if (repeat) {
                return NONE;
            }
            if (running) {
                return LOCKED;
            }
            return is(key, code, 'c') ? CYCLE_MODE : TOGGLE_LIF;
        }
        if (!running) {
            return is(key, code, 'n') && !repeat ? NEW_SEED : NONE;
        }
        if (is(key, code, 'r')) {
            return RESTART;
        }
        return repeat ? NONE : LANE;
    }

    /**
     * What a click on the AUTOPLAY button does. {@code detail} is
     * UIEvent.detail: the click count for a mouse / touch click, 0 for a click
     * synthesised by keyboard activation (or element.click()).
     */
    public static int buttonClick(int detail, boolean running) {
        if (detail == 0) {
            return NONE;
        }
        return running ? LOCKED : CYCLE_MODE;
    }
}
