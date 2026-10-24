package com.fruitfly.games.rhythm.irc;

/**
 * {@code /llm <text>} chat mode for the TeaVM left CLI. The browser never
 * talks to a model: it sends one WebSocket text frame to the loopback bridge
 * ({@code ws://127.0.0.1:6669/cli}, or the Pages WSS under Option B), and the
 * bridge forwards to a GGUF model served by llama.cpp's {@code llama-server}
 * on {@code 127.0.0.1}.
 *
 * <p>Wire format (newline-separated; JSON blocks carry no raw newlines):
 * <pre>
 * /llm &lt;prompt on one line&gt;
 * #neuro {…NeuronSnapshot JSON…}
 * #feedback {…TracebackFeedback JSON…}
 * </pre>
 * A bare {@code /llm hi} (no blocks) is also valid; the bridge then says the
 * snapshot is missing rather than inventing one.
 */
public final class LlmCli {
    public static final String VERB = "/llm";
    public static final String NEURO_TAG = "#neuro ";
    public static final String FEEDBACK_TAG = "#feedback ";
    /** Cap on the user's prompt text (chars) before it goes on the wire. */
    public static final int MAX_PROMPT = 2000;

    private LlmCli() {
    }

    public static boolean isLlmLine(String raw) {
        if (raw == null) {
            return false;
        }
        String t = raw.trim().toLowerCase();
        return t.equals(VERB) || t.startsWith(VERB + " ");
    }

    /** Prompt text after {@code /llm}, on one line, capped. */
    public static String prompt(String raw) {
        String t = raw == null ? "" : raw.trim();
        if (t.toLowerCase().startsWith(VERB)) {
            t = t.substring(VERB.length()).trim();
        }
        t = t.replace('\r', ' ').replace('\n', ' ');
        return TracebackFeedback.trim(t, MAX_PROMPT);
    }

    /** Build the frame sent to the bridge. Null/blank blocks are omitted. */
    public static String wire(String raw, String neuroJson, String feedbackJson) {
        StringBuilder b = new StringBuilder(VERB).append(' ').append(prompt(raw));
        if (neuroJson != null && !neuroJson.isEmpty()) {
            b.append('\n').append(NEURO_TAG).append(oneLine(neuroJson));
        }
        if (feedbackJson != null && !feedbackJson.isEmpty()) {
            b.append('\n').append(FEEDBACK_TAG).append(oneLine(feedbackJson));
        }
        return b.toString();
    }

    private static String oneLine(String s) {
        return s.replace('\r', ' ').replace('\n', ' ');
    }

    public static String offlineLine() {
        return CliLines.format(CliLines.KIND_SYSTEM,
                "llm offline — bridge not connected (start sovereign-irc-bridge on "
                        + IrcBridgeConfig.LOOPBACK_CLI_HOST + ":" + IrcBridgeConfig.LOOPBACK_CLI_PORT
                        + ", then llama-server on 127.0.0.1:8081)");
    }

    public static String helpLine() {
        return CliLines.format(CliLines.KIND_SYSTEM,
                "llm: /llm <text> · GGUF via llama-server 127.0.0.1:8081 · sends spike snapshot + traceback feedback");
    }
}
