package com.fruitfly.games.rhythm.logic;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Reads a chart in this JSON format into a {@link LoadedChart}:
 *
 * <pre>
 * {
 *   "metadata": { "title": "...", "artist": "...", "bpm": 120, "offset_ms": 0, "audio": "optional.ogg" },
 *   "notes": [ { "time_ms": 1000, "lane": 0 }, ... ]
 * }
 * </pre>
 *
 * Rules: title and artist are strings; bpm is a number in (0, 1000];
 * offset_ms is an integer in [-600000, 600000]; audio is optional. Each note
 * needs an integer time_ms in [0, 86400000] and an integer lane in
 * 0..{@value RhythmGame#LANES}-1. Notes may be in any order (they're stably
 * sorted by time); the same lane twice at the same time is rejected. Unknown
 * keys are ignored. Any problem throws {@link ChartFormatException} naming
 * the field, e.g. {@code notes[3].lane: must be an integer 0..3, got 5}.
 *
 * The JSON reader is a small strict RFC 8259 parser written here, so the
 * logic package stays JDK-only and runs the same on the JVM and in TeaVM.
 */
public final class ChartJson {
    static final long MAX_TIME_MS = 86_400_000L;
    static final long MAX_ABS_OFFSET_MS = 600_000L;
    static final double MAX_BPM = 1000.0;
    static final int MAX_DEPTH = 64;

    private ChartJson() {
    }

    public static LoadedChart parse(String json) {
        if (json == null) {
            throw new ChartFormatException("chart text is null");
        }
        Object root = new Reader(json).readDocument();
        Map<String, Object> top = object(root, "chart");
        Map<String, Object> meta = object(required(top, "metadata", "chart"), "metadata");
        String title = string(required(meta, "title", "metadata"), "metadata.title");
        String artist = string(required(meta, "artist", "metadata"), "metadata.artist");
        double bpm = number(required(meta, "bpm", "metadata"), "metadata.bpm");
        if (!(bpm > 0.0 && bpm <= MAX_BPM)) {
            throw new ChartFormatException("metadata.bpm: must be > 0 and <= 1000, got " + fmt(bpm));
        }
        long offset = integer(required(meta, "offset_ms", "metadata"), "metadata.offset_ms",
                -MAX_ABS_OFFSET_MS, MAX_ABS_OFFSET_MS);
        String audio = null;
        if (meta.containsKey("audio") && meta.get("audio") != null) {
            audio = string(meta.get("audio"), "metadata.audio");
            if (audio.isEmpty()) {
                audio = null;
            }
        }
        Object notesVal = required(top, "notes", "chart");
        if (!(notesVal instanceof List)) {
            throw new ChartFormatException("notes: must be an array, got " + kind(notesVal));
        }
        List<?> arr = (List<?>) notesVal;
        List<Note> notes = new ArrayList<>(arr.size());
        for (int i = 0; i < arr.size(); i++) {
            String where = "notes[" + i + "]";
            Map<String, Object> n = object(arr.get(i), where);
            long t = integer(required(n, "time_ms", where), where + ".time_ms", 0, MAX_TIME_MS);
            long lane = integer(required(n, "lane", where), where + ".lane", 0, RhythmGame.LANES - 1);
            notes.add(new Note((int) lane, t));
        }
        NoteChart chart;
        try {
            chart = NoteChart.fromNotes(notes);
        } catch (IllegalArgumentException e) {
            throw new ChartFormatException("notes: " + e.getMessage());
        }
        return new LoadedChart(title, artist, bpm, offset, audio, chart);
    }

    // ---- field helpers ----

    private static Object required(Map<String, Object> obj, String key, String where) {
        if (!obj.containsKey(key)) {
            throw new ChartFormatException(where + ": missing \"" + key + "\"");
        }
        return obj.get(key);
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> object(Object v, String where) {
        if (!(v instanceof Map)) {
            throw new ChartFormatException(where + ": must be an object, got " + kind(v));
        }
        return (Map<String, Object>) v;
    }

    private static String string(Object v, String where) {
        if (!(v instanceof String)) {
            throw new ChartFormatException(where + ": must be a string, got " + kind(v));
        }
        return (String) v;
    }

    private static double number(Object v, String where) {
        if (!(v instanceof Double)) {
            throw new ChartFormatException(where + ": must be a number, got " + kind(v));
        }
        return (Double) v;
    }

    private static long integer(Object v, String where, long min, long max) {
        double d = number(v, where);
        if (d != Math.floor(d) || d < min || d > max) {
            String range = min == 0 && max == RhythmGame.LANES - 1
                    ? "an integer 0.." + max : "an integer in [" + min + ", " + max + "]";
            throw new ChartFormatException(where + ": must be " + range + ", got " + fmt(d));
        }
        return (long) d;
    }

    private static String kind(Object v) {
        if (v == null) {
            return "null";
        }
        if (v instanceof String) {
            return "a string";
        }
        if (v instanceof Double) {
            return "a number";
        }
        if (v instanceof Boolean) {
            return "a boolean";
        }
        if (v instanceof List) {
            return "an array";
        }
        return "an object";
    }

    private static String fmt(double d) {
        return d == Math.floor(d) && Math.abs(d) < 1e15 ? Long.toString((long) d) : Double.toString(d);
    }

    // ---- strict JSON reader: objects -> LinkedHashMap, arrays -> ArrayList, numbers -> Double ----

    static final class Reader {
        private final String s;
        private int pos;
        private int depth;

        Reader(String s) {
            this.s = s;
        }

        Object readDocument() {
            skipWs();
            if (pos >= s.length()) {
                throw err("empty document");
            }
            Object v = readValue();
            skipWs();
            if (pos < s.length()) {
                throw err("unexpected trailing text");
            }
            return v;
        }

        private ChartFormatException err(String msg) {
            int line = 1;
            int col = 1;
            for (int i = 0; i < pos && i < s.length(); i++) {
                if (s.charAt(i) == '\n') {
                    line++;
                    col = 1;
                } else {
                    col++;
                }
            }
            return new ChartFormatException("invalid JSON at line " + line + ", column " + col + ": " + msg);
        }

        private void skipWs() {
            while (pos < s.length()) {
                char c = s.charAt(pos);
                if (c == ' ' || c == '\t' || c == '\n' || c == '\r') {
                    pos++;
                } else {
                    break;
                }
            }
        }

        private Object readValue() {
            if (pos >= s.length()) {
                throw err("unexpected end of input");
            }
            char c = s.charAt(pos);
            switch (c) {
                case '{':
                    return readObject();
                case '[':
                    return readArray();
                case '"':
                    return readString();
                case 't':
                    literal("true");
                    return Boolean.TRUE;
                case 'f':
                    literal("false");
                    return Boolean.FALSE;
                case 'n':
                    literal("null");
                    return null;
                default:
                    if (c == '-' || (c >= '0' && c <= '9')) {
                        return readNumber();
                    }
                    throw err("unexpected character '" + c + "'");
            }
        }

        private void literal(String word) {
            if (!s.startsWith(word, pos)) {
                throw err("expected " + word);
            }
            pos += word.length();
        }

        private void enter() {
            if (++depth > MAX_DEPTH) {
                throw err("nesting deeper than " + MAX_DEPTH);
            }
        }

        private Map<String, Object> readObject() {
            enter();
            pos++; // {
            Map<String, Object> m = new LinkedHashMap<>();
            skipWs();
            if (pos < s.length() && s.charAt(pos) == '}') {
                pos++;
                depth--;
                return m;
            }
            while (true) {
                skipWs();
                if (pos >= s.length() || s.charAt(pos) != '"') {
                    throw err("expected a string key");
                }
                String key = readString();
                if (m.containsKey(key)) {
                    throw err("duplicate key \"" + key + "\"");
                }
                skipWs();
                if (pos >= s.length() || s.charAt(pos) != ':') {
                    throw err("expected ':'");
                }
                pos++;
                skipWs();
                m.put(key, readValue());
                skipWs();
                if (pos >= s.length()) {
                    throw err("unterminated object");
                }
                char c = s.charAt(pos++);
                if (c == '}') {
                    depth--;
                    return m;
                }
                if (c != ',') {
                    pos--;
                    throw err("expected ',' or '}'");
                }
            }
        }

        private List<Object> readArray() {
            enter();
            pos++; // [
            List<Object> a = new ArrayList<>();
            skipWs();
            if (pos < s.length() && s.charAt(pos) == ']') {
                pos++;
                depth--;
                return a;
            }
            while (true) {
                skipWs();
                a.add(readValue());
                skipWs();
                if (pos >= s.length()) {
                    throw err("unterminated array");
                }
                char c = s.charAt(pos++);
                if (c == ']') {
                    depth--;
                    return a;
                }
                if (c != ',') {
                    pos--;
                    throw err("expected ',' or ']'");
                }
            }
        }

        private String readString() {
            pos++; // opening quote
            StringBuilder b = new StringBuilder();
            while (true) {
                if (pos >= s.length()) {
                    throw err("unterminated string");
                }
                char c = s.charAt(pos++);
                if (c == '"') {
                    return b.toString();
                }
                if (c < 0x20) {
                    pos--;
                    throw err("control character in string");
                }
                if (c != '\\') {
                    b.append(c);
                    continue;
                }
                if (pos >= s.length()) {
                    throw err("unterminated escape");
                }
                char e = s.charAt(pos++);
                switch (e) {
                    case '"':
                    case '\\':
                    case '/':
                        b.append(e);
                        break;
                    case 'b':
                        b.append('\b');
                        break;
                    case 'f':
                        b.append('\f');
                        break;
                    case 'n':
                        b.append('\n');
                        break;
                    case 'r':
                        b.append('\r');
                        break;
                    case 't':
                        b.append('\t');
                        break;
                    case 'u':
                        if (pos + 4 > s.length()) {
                            throw err("bad \\u escape");
                        }
                        int code = 0;
                        for (int k = 0; k < 4; k++) {
                            int d = Character.digit(s.charAt(pos + k), 16);
                            if (d < 0) {
                                throw err("bad \\u escape");
                            }
                            code = code * 16 + d;
                        }
                        pos += 4;
                        b.append((char) code);
                        break;
                    default:
                        pos--;
                        throw err("bad escape '\\" + e + "'");
                }
            }
        }

        private Double readNumber() {
            int start = pos;
            if (s.charAt(pos) == '-') {
                pos++;
            }
            if (pos >= s.length()) {
                throw err("bad number");
            }
            if (s.charAt(pos) == '0') {
                pos++;
            } else if (s.charAt(pos) >= '1' && s.charAt(pos) <= '9') {
                while (pos < s.length() && Character.isDigit(s.charAt(pos))) {
                    pos++;
                }
            } else {
                throw err("bad number");
            }
            if (pos < s.length() && s.charAt(pos) == '.') {
                pos++;
                int d0 = pos;
                while (pos < s.length() && Character.isDigit(s.charAt(pos))) {
                    pos++;
                }
                if (pos == d0) {
                    throw err("bad number: digits expected after '.'");
                }
            }
            if (pos < s.length() && (s.charAt(pos) == 'e' || s.charAt(pos) == 'E')) {
                pos++;
                if (pos < s.length() && (s.charAt(pos) == '+' || s.charAt(pos) == '-')) {
                    pos++;
                }
                int d0 = pos;
                while (pos < s.length() && Character.isDigit(s.charAt(pos))) {
                    pos++;
                }
                if (pos == d0) {
                    throw err("bad number: exponent digits expected");
                }
            }
            double d = Double.parseDouble(s.substring(start, pos));
            if (Double.isInfinite(d) || Double.isNaN(d)) {
                pos = start;
                throw err("number out of range");
            }
            return d;
        }
    }
}
