package com.fruitfly.games.rhythm.logic;

/**
 * Who plays: the control modes cycled by key C and by the on-screen AUTOPLAY
 * button (both call the same {@link #cycle}), plus key B's LIF toggle.
 * Modes only change between songs, so a score is all-brain or all-human.
 */
public final class ControlMode {
    public static final int OFF = 0;
    public static final int LIF = 1;
    public static final int CONNECTOME = 2;
    public static final int ASSIST_LIF = 3;
    public static final int ASSIST_CONNECTOME = 4;
    public static final int COUNT = 5;

    private static final String[] BUTTON = {
        "AUTOPLAY: OFF",
        "AUTOPLAY: LIF FLY",
        "AUTOPLAY: CONNECTOME FLY",
        "AUTOPLAY: ASSIST \u00b7 LIF FLY",
        "AUTOPLAY: ASSIST \u00b7 CONNECTOME FLY",
    };
    private static final String[] HUD = {
        "autoplay off", "LIF autoplay ON", "connectome autoplay ON",
        "assist ON (LIF fly)", "assist ON (connectome fly)",
    };

    /** Shown on the stage when C / B / the AUTOPLAY button is used mid-song. */
    public static final String LOCK_HINT = "Autoplay locked during song - press R to restart";
    /** How long the lock hint stays up, ms (page frame time). */
    public static final double LOCK_HINT_MS = 2200;
    /** Button tooltip between songs and while locked. */
    public static final String TITLE_IDLE = "Autoplay mode (same as key C; changes between songs only)";
    public static final String TITLE_LOCKED = "Locked during song - press R to restart, then change mode";

    private ControlMode() {
    }

    /** C / button: off -> LIF -> connectome -> assist LIF -> assist connectome -> off; unchanged while a song runs. */
    public static int cycle(int mode, boolean running) {
        check(mode);
        return running ? mode : (mode + 1) % COUNT;
    }

    /** B: LIF autoplay on/off (any other mode goes to LIF); unchanged while a song runs. */
    public static int toggleLif(int mode, boolean running) {
        check(mode);
        if (running) {
            return mode;
        }
        return mode == LIF ? OFF : LIF;
    }

    public static boolean isAssist(int mode) {
        return mode == ASSIST_LIF || mode == ASSIST_CONNECTOME;
    }

    /** The fly presses every key itself (human lane keys are ignored). */
    public static boolean isFullAutoplay(int mode) {
        return mode == LIF || mode == CONNECTOME;
    }

    /** Text on the on-screen AUTOPLAY button. */
    public static String buttonLabel(int mode) {
        check(mode);
        return BUTTON[mode];
    }

    /**
     * Button text for a mode, with the lock shown while a song runs:
     * "AUTOPLAY: X" becomes "LOCKED: X" (never longer than the idle label,
     * so the button size is unchanged).
     */
    public static String buttonLabel(int mode, boolean running) {
        String s = buttonLabel(mode);
        return running ? "LOCKED: " + s.substring("AUTOPLAY: ".length()) : s;
    }

    public static String buttonTitle(boolean running) {
        return running ? TITLE_LOCKED : TITLE_IDLE;
    }

    private static final String[] ID = {"off", "lif", "connectome", "assist-lif", "assist-connectome"};

    /** Short id (window.__rhythmDebug.mode()). */
    public static String id(int mode) {
        check(mode);
        return ID[mode];
    }

    /** Mode line in the right-hand HUD. */
    public static String hudText(int mode) {
        check(mode);
        return HUD[mode];
    }

    /** Longest button label, in characters (for sizing the button). */
    public static int longestButtonLabel() {
        int n = 0;
        for (String s : BUTTON) {
            n = Math.max(n, s.length());
        }
        return n;
    }

    private static void check(int mode) {
        if (mode < 0 || mode >= COUNT) {
            throw new IllegalArgumentException("mode out of range: " + mode);
        }
    }
}
