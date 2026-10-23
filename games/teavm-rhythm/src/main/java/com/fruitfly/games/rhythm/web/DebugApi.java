package com.fruitfly.games.rhythm.web;

import org.teavm.jso.JSBody;
import org.teavm.jso.JSFunctor;
import org.teavm.jso.JSObject;

/**
 * window.__rhythmDebug: a frozen, read-only view of the moves list.
 *
 * <pre>
 *   version          "rhythm-moves/1"
 *   moves()          last 64 rows (fresh copies, oldest first)
 *   first20()        first 20 rows of the song
 *   count()          rows written so far (chain length)
 *   mode()           "off" | "lif" | "connectome" | "assist-lif" | "assist-connectome"
 *   clock()          song time now, ms (the smoothed clock the stage draws with)
 *   verify(rows?)    no argument: re-derive math_origin + hash chain of the kept rows in Java;
 *                    with rows: re-hash those rows here -> {ok, firstBad, checked}
 *   sha256(s)        the game's SHA-256 (hex), for recomputing a row's hash
 * </pre>
 * Rows are JSON copies: changing them changes nothing in the game.
 */
final class DebugApi {
    static final String VERSION = "rhythm-moves/1";

    @JSFunctor
    interface Text extends JSObject {
        String get();
    }

    @JSFunctor
    interface Num extends JSObject {
        double get();
    }

    @JSFunctor
    interface Hash extends JSObject {
        String hash(String s);
    }

    private DebugApi() {
    }

    @JSBody(params = {"version", "moves", "first", "count", "mode", "clock", "verifyKept", "sha"}, script = ""
            + "if (typeof window === 'undefined') return;"
            + "var Z = '0000000000000000000000000000000000000000000000000000000000000000';"
            + "function na(v) { return v === null || v === undefined ? 'na' : String(v); }"
            + "function pre(m, prev) { return 'rhythm-move/v1|prev=' + prev + '|i=' + m.i + '|t=' + m.t + '|lane=' + m.lane"
            + "  + '|delta=' + na(m.delta) + '|who=' + m.who + '|press=' + na(m.press) + '|dt=' + na(m.dt)"
            + "  + '|judge=' + m.judge + '|fired=' + (m.fired === null || m.fired === undefined ? 'na' : m.fired ? 'yes' : 'no')"
            + "  + '|lat=' + na(m.lat) + '|' + m.math_origin; }"
            + "function check(rows) {"
            + "  for (var k = 0; k < rows.length; k++) { var m = rows[k];"
            + "    var want = k > 0 ? rows[k - 1].hash : (m.i === 0 ? Z : m.prev);"
            + "    if (m.prev !== want || sha(pre(m, m.prev)) !== m.hash) return {ok: false, firstBad: m.i, index: k, checked: k}; }"
            + "  return {ok: true, firstBad: null, index: -1, checked: rows.length}; }"
            + "var api = {"
            + "  version: version,"
            + "  moves: function () { return JSON.parse(moves()); },"
            + "  first20: function () { return JSON.parse(first()); },"
            + "  count: function () { return count() | 0; },"
            + "  mode: function () { return String(mode()); },"
            + "  clock: function () { return +clock(); },"
            + "  sha256: function (s) { return String(sha(String(s))); },"
            + "  verify: function (rows) {"
            + "    if (rows) return check(rows);"
            + "    var bad = verifyKept() | 0, a = check(JSON.parse(first())), b = check(JSON.parse(moves()));"
            + "    var fb = bad >= 0 ? bad : !a.ok ? a.firstBad : !b.ok ? b.firstBad : null;"
            + "    return {ok: fb === null, firstBad: fb, checked: count() | 0}; }"
            + "};"
            + "if (Object.freeze) Object.freeze(api);"
            + "try { Object.defineProperty(window, '__rhythmDebug', {value: api, writable: false, enumerable: false, configurable: true}); }"
            + "catch (e) { window.__rhythmDebug = api; }")
    static native void install(String version, Text moves, Text first, Num count, Text mode, Num clock, Num verifyKept, Hash sha);
}
