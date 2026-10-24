package com.fruitfly.games.rhythm.irc;

/**
 * Pure formatting for the TeaVM left CLI (System / Engine / User).
 * No sockets — safe for JVM unit tests.
 *
 * <p>Cosmic Alignment (Option B):
 * <ul>
 *   <li>local / CI ({@code 127.0.0.1}, {@code localhost}):
 *       {@code UI → ws://127.0.0.1:6680/cli → bridge → irc.abjects.net:6669}</li>
 *   <li>GitHub Pages / production host:
 *       {@code UI → wss://bridge.axiomiccoreness.com/cli → bridge → irc.abjects.net:6669}</li>
 * </ul>
 * Browser never dials abjects or {@code 0.0.0.0} directly.
 */
public final class CliLines {
    public static final String KIND_SYSTEM = "System";
    public static final String KIND_ENGINE = "Engine";
    public static final String KIND_USER = "User";
    /** Traceback / pythonIDE error lines in chat history. */
    public static final String KIND_TRACEBACK = "Traceback";

    /** Contract URL for the loopback CLI (TeaVM local/CI; never 0.0.0.0). */
    public static final String LOOPBACK_WS = "ws://127.0.0.1:6680/cli";
    /** Pages / production WSS bridge (Option B). Exact URL only. */
    public static final String PAGES_WSS = "wss://bridge.axiomiccoreness.com/cli";
    /** Remote IRC label behind the bridge (UI ports slot 6669). */
    public static final String REMOTE_IRC = "irc.abjects.net:6669";

    private CliLines() {
    }

    public static String format(String kind, String body) {
        if (kind == null || kind.isEmpty()) {
            kind = KIND_SYSTEM;
        }
        if (body == null) {
            body = "";
        }
        return "[" + kind + "] " + body;
    }

    /**
     * Option B hostname → CLI WebSocket URL.
     * <p>{@code 127.0.0.1} / {@code localhost} (and IPv6 loopback) → {@link #LOOPBACK_WS}.
     * Any other host (e.g. GitHub Pages) → {@link #PAGES_WSS}.
     * Null / blank hostname defaults to {@link #LOOPBACK_WS} (local-first for JVM tests
     * and headless smoke without a browser location).
     */
    public static String resolveCliWsUrl(String hostname) {
        if (hostname == null) {
            return LOOPBACK_WS;
        }
        String h = hostname.trim().toLowerCase();
        if (h.isEmpty()) {
            return LOOPBACK_WS;
        }
        if (h.equals("127.0.0.1")
                || h.equals("localhost")
                || h.equals("::1")
                || h.equals("[::1]")) {
            return LOOPBACK_WS;
        }
        return PAGES_WSS;
    }

    /** True only for the Cosmic Alignment loopback CLI URL (127.0.0.1 / ::1, not 0.0.0.0). */
    public static boolean isLoopbackCliUrl(String url) {
        if (url == null) {
            return false;
        }
        String u = url.trim();
        return u.equals(LOOPBACK_WS)
                || u.startsWith("ws://127.0.0.1:6680/")
                || u.startsWith("ws://[::1]:6680/");
    }

    /**
     * Allowed dial targets: loopback CLI URLs <strong>or</strong> exact {@link #PAGES_WSS}.
     * Rejects {@code ws://0.0.0.0…}, direct abjects, and other wss hosts.
     */
    public static boolean isAllowedCliUrl(String url) {
        if (url == null) {
            return false;
        }
        String u = url.trim();
        return isLoopbackCliUrl(u) || u.equals(PAGES_WSS);
    }

    public static String bootSystemLine() {
        return format(KIND_SYSTEM, "TeaVM CLI → " + LOOPBACK_WS + " → " + REMOTE_IRC);
    }

    /** Boot hint naming Option B Pages WSS (vs local loopback contract). */
    public static String pagesHttpsHint() {
        return format(KIND_SYSTEM,
                "Pages / production dials " + PAGES_WSS
                        + "; local/CI dials " + LOOPBACK_WS);
    }
}
