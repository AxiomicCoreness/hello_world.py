package com.fruitfly.games.rhythm.client.ide;

import com.fruitfly.games.rhythm.client.CliLines;
import com.fruitfly.games.rhythm.logic.Json;
import java.util.ArrayList;
import java.util.List;

/**
 * The {@code /llm} chat's feedback signal (the "carrot on the stick"): the
 * most recent traceback reports that reached the CLI history, instead of any
 * dopamine / reward variable. Every chat line is fed through
 * {@link #accept(String)}; a run of {@code [Traceback] …} lines (from the
 * bridge's real pythonIDE tracebacks or {@link PythonIdeCli}'s offline ones)
 * becomes one report once a non-traceback line follows or
 * {@link #flush()} is called.
 *
 * <p>Each report is trimmed to the exception type, its message (at most
 * {@link #MAX_MESSAGE} chars) and the last {@link #MAX_FRAMES} frames
 * ({@code file:line in func}). Only the last {@link #MAX_REPORTS} reports are
 * kept, and {@link #toJson()} drops the oldest until the block fits in
 * {@link #MAX_JSON} chars. Pure Java: no TeaVM types, JVM-testable.
 */
public final class TracebackFeedback {
    public static final int MAX_REPORTS = 3;
    public static final int MAX_FRAMES = 3;
    public static final int MAX_MESSAGE = 200;
    public static final int MAX_JSON = 1200;
    private static final String TB_PREFIX = "[" + CliLines.KIND_TRACEBACK + "] ";

    private final List<Report> reports = new ArrayList<>();
    private final List<String> pending = new ArrayList<>();
    private long seen;

    /** Feed one chat-history line ({@code [Kind] body}). */
    public void accept(String line) {
        if (line == null) {
            return;
        }
        if (line.startsWith(TB_PREFIX)) {
            pending.add(line.substring(TB_PREFIX.length()));
            return;
        }
        flush();
    }

    /** Close a traceback still being collected. */
    public void flush() {
        if (pending.isEmpty()) {
            return;
        }
        Report r = parse(pending, "cli");
        pending.clear();
        if (r != null) {
            add(r);
        }
    }

    /** Add a report directly (e.g. a WebSocket send error). */
    public void add(String type, String message, List<String> frames, String origin) {
        add(new Report(trim(type, 80), trim(message, MAX_MESSAGE), lastFrames(frames), origin));
    }

    private void add(Report r) {
        reports.add(r);
        seen++;
        while (reports.size() > MAX_REPORTS) {
            reports.remove(0);
        }
    }

    public int size() {
        return reports.size();
    }

    /** Reports ever recorded (kept or rotated out). */
    public long seen() {
        return seen;
    }

    /** Parse traceback body lines (without the {@code [Traceback] } tag). */
    static Report parse(List<String> body, String origin) {
        List<String> frames = new ArrayList<>();
        String type = null;
        String message = null;
        String lastText = null;
        for (String raw : body) {
            String s = raw == null ? "" : raw.trim();
            if (s.isEmpty() || s.startsWith("Traceback (most recent call last)")) {
                continue;
            }
            if (s.startsWith("File \"")) {
                frames.add(frame(s));
                continue;
            }
            lastText = s;
            int colon = s.indexOf(':');
            if (colon > 0 && isTypeName(s.substring(0, colon))) {
                type = s.substring(0, colon);
                message = s.substring(colon + 1).trim();
            }
        }
        if (type == null) {
            if (lastText == null && frames.isEmpty()) {
                return null;
            }
            type = "Error";
            message = lastText == null ? "" : lastText;
        }
        return new Report(trim(type, 80), trim(message, MAX_MESSAGE), lastFrames(frames), origin);
    }

    /** {@code File "/a/b/x.py", line 12, in f} → {@code x.py:12 in f}. */
    static String frame(String s) {
        int q1 = s.indexOf('"');
        int q2 = q1 < 0 ? -1 : s.indexOf('"', q1 + 1);
        if (q2 < 0) {
            return trim(s, 120);
        }
        String file = s.substring(q1 + 1, q2);
        int slash = Math.max(file.lastIndexOf('/'), file.lastIndexOf('\\'));
        if (slash >= 0) {
            file = file.substring(slash + 1);
        }
        String rest = s.substring(q2 + 1);
        String lineNo = "";
        int li = rest.indexOf("line ");
        if (li >= 0) {
            int e = li + 5;
            while (e < rest.length() && Character.isDigit(rest.charAt(e))) {
                e++;
            }
            lineNo = rest.substring(li + 5, e);
        }
        String fn = "";
        int in = rest.indexOf(", in ");
        if (in >= 0) {
            fn = rest.substring(in + 5).trim();
        }
        return trim(file + (lineNo.isEmpty() ? "" : ":" + lineNo) + (fn.isEmpty() ? "" : " in " + fn), 120);
    }

    private static boolean isTypeName(String s) {
        if (s.isEmpty() || s.length() > 80) {
            return false;
        }
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (!(Character.isLetterOrDigit(c) || c == '_' || c == '.')) {
                return false;
            }
        }
        String last = s.substring(s.lastIndexOf('.') + 1);
        return !last.isEmpty() && Character.isUpperCase(last.charAt(0));
    }

    private static List<String> lastFrames(List<String> frames) {
        List<String> out = new ArrayList<>();
        if (frames == null) {
            return out;
        }
        for (int i = Math.max(0, frames.size() - MAX_FRAMES); i < frames.size(); i++) {
            out.add(frames.get(i));
        }
        return out;
    }

    public static String trim(String s, int max) {
        if (s == null) {
            return "";
        }
        return s.length() <= max ? s : s.substring(0, max - 1) + "…";
    }

    /** {@code {"kind":"traceback","reports":[…],"dropped":n}}, at most {@link #MAX_JSON} chars. */
    public String toJson() {
        flush();
        int from = 0;
        String out = render(from);
        while (out.length() > MAX_JSON && from < reports.size()) {
            from++;
            out = render(from);
        }
        return out;
    }

    private String render(int from) {
        StringBuilder b = new StringBuilder(256);
        b.append("{\"kind\":\"traceback\",\"reports\":[");
        for (int i = from; i < reports.size(); i++) {
            Report r = reports.get(i);
            if (i > from) {
                b.append(',');
            }
            b.append("{\"type\":").append(Json.str(r.type))
                    .append(",\"message\":").append(Json.str(r.message))
                    .append(",\"origin\":").append(Json.str(r.origin))
                    .append(",\"frames\":[");
            for (int k = 0; k < r.frames.size(); k++) {
                if (k > 0) {
                    b.append(',');
                }
                b.append(Json.str(r.frames.get(k)));
            }
            b.append("]}");
        }
        b.append("],\"dropped\":").append(seen - (reports.size() - from)).append('}');
        return b.toString();
    }

    /** One trimmed traceback report. */
    static final class Report {
        final String type;
        final String message;
        final List<String> frames;
        final String origin;

        Report(String type, String message, List<String> frames, String origin) {
            this.type = type;
            this.message = message;
            this.frames = frames;
            this.origin = origin == null ? "cli" : origin;
        }
    }
}
