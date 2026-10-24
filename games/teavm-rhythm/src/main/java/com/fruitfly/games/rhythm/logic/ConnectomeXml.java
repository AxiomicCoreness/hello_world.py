package com.fruitfly.games.rhythm.logic;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Tiny pure-Java reader for the project-local connectome XML
 * (src/main/resources/connectome.xsd at the repo root). TeaVM has no
 * javax.xml, so this reads just that format by hand:
 *
 * <pre>
 * &lt;hemibrain&gt;
 *   &lt;neuron id="A" region="mushroom body"/&gt;
 *   &lt;connection from="A" to="B" weight="1.0" delayMs="2.5"/&gt;
 * &lt;/hemibrain&gt;
 * </pre>
 *
 * Semantics follow com.fruitfly.brain.ConnectomeLoader: ids trimmed,
 * non-empty, unique, indexed in document order; from/to must name declared
 * neurons (any order); weight required and finite; delayMs optional
 * (default {@value #DEFAULT_DELAY_MS}), finite and &gt; 0; self-loops allowed;
 * a repeated (from, to) pair rejected; CSR rows by source, document order.
 * region is the DRAFT optional label from the xsd proposal.
 *
 * Like the xsd (and stricter than the loader) it rejects unknown elements,
 * unknown attributes, nesting and non-whitespace text. DOCTYPE, CDATA and
 * namespaces are refused. Accepts the XML declaration, comments and
 * processing instructions, both quote styles, and the five predefined
 * entities plus numeric character references.
 */
public final class ConnectomeXml {
    public static final double DEFAULT_DELAY_MS = 1.0;

    private final String s;
    private int pos;

    private ConnectomeXml(String s) {
        this.s = s;
    }

    /** Parse; throws IllegalArgumentException with a position-specific message. */
    public static Circuit parse(String xml) {
        if (xml == null) {
            throw new IllegalArgumentException("connectome: no text");
        }
        return new ConnectomeXml(xml).document();
    }

    private Circuit document() {
        if (s.startsWith("\uFEFF")) {
            pos = 1;
        }
        misc();
        if (!s.startsWith("<hemibrain", pos)) {
            throw err("root element must be <hemibrain>");
        }
        Map<String, String> rootAttrs = new HashMap<>();
        boolean selfClosing = tag("hemibrain", rootAttrs);
        for (String k : rootAttrs.keySet()) {
            if (!k.startsWith("xmlns:") && !k.startsWith("xsi:")) {
                throw err("<hemibrain> has unknown attribute '" + k + "'");
            }
        }
        List<String> ids = new ArrayList<>();
        List<String> regions = new ArrayList<>();
        List<String[]> conns = new ArrayList<>();
        Map<String, Integer> index = new HashMap<>();
        if (!selfClosing) {
            while (true) {
                skipContent();
                if (pos >= s.length()) {
                    throw err("missing </hemibrain>");
                }
                if (s.startsWith("</", pos)) {
                    pos += 2;
                    String name = name();
                    ws();
                    expect('>');
                    if (!"hemibrain".equals(name)) {
                        throw err("unexpected </" + name + ">");
                    }
                    break;
                }
                int at = pos;
                pos++;
                String name = name();
                pos = at;
                Map<String, String> a = new HashMap<>();
                if ("neuron".equals(name)) {
                    child("neuron", a);
                    allow(a, "neuron #" + ids.size(), "id", "region");
                    String id = required(a, "id", "neuron #" + ids.size()).trim();
                    if (id.isEmpty()) {
                        throw err("neuron #" + ids.size() + " has a blank id");
                    }
                    if (index.containsKey(id)) {
                        throw err("duplicate neuron id '" + id + "'");
                    }
                    index.put(id, ids.size());
                    ids.add(id);
                    String r = a.get("region");
                    if (r != null && r.trim().isEmpty()) {
                        throw err("neuron '" + id + "' has a blank region");
                    }
                    regions.add(r == null ? null : r.trim());
                } else if ("connection".equals(name)) {
                    child("connection", a);
                    String where = "connection #" + conns.size();
                    allow(a, where, "from", "to", "weight", "delayMs");
                    conns.add(new String[] {required(a, "from", where).trim(), required(a, "to", where).trim(),
                        required(a, "weight", where), a.get("delayMs"), where});
                } else {
                    throw err("unknown element <" + name + ">");
                }
            }
        }
        misc();
        if (pos != s.length()) {
            throw err("content after </hemibrain>");
        }
        int n = ids.size();
        int m = conns.size();
        // Validate in document order (first bad connection wins, as before), then
        // build CSR with a stable counting sort by source: O(V + E) overall.
        int[] pres = new int[m];
        int[] posts = new int[m];
        double[] ws = new double[m];
        double[] ds = new double[m];
        PairSet seen = new PairSet(m);
        for (int e = 0; e < m; e++) {
            String[] c = conns.get(e);
            Integer pre = index.get(c[0]);
            if (pre == null) {
                throw new IllegalArgumentException(c[4] + " references unknown source neuron '" + c[0] + "'");
            }
            Integer post = index.get(c[1]);
            if (post == null) {
                throw new IllegalArgumentException(c[4] + " references unknown target neuron '" + c[1] + "'");
            }
            double we = number(c[2], "weight", c[4]);
            double de = c[3] == null ? DEFAULT_DELAY_MS : number(c[3], "delayMs", c[4]);
            if (!(de > 0.0)) {
                throw new IllegalArgumentException(c[4] + " delayMs must be > 0, got " + de);
            }
            if (!seen.add(pre, post)) {
                throw new IllegalArgumentException("duplicate connection " + c[0] + " -> " + c[1]);
            }
            pres[e] = pre;
            posts[e] = post;
            ws[e] = we;
            ds[e] = de;
        }
        int[] rowPtr = new int[n + 1];
        for (int e = 0; e < m; e++) {
            rowPtr[pres[e] + 1]++;
        }
        for (int i = 0; i < n; i++) {
            rowPtr[i + 1] += rowPtr[i];
        }
        int[] fill = new int[n];
        System.arraycopy(rowPtr, 0, fill, 0, n);
        int[] col = new int[m];
        double[] w = new double[m];
        double[] d = new double[m];
        for (int e = 0; e < m; e++) {
            int k = fill[pres[e]]++;
            col[k] = posts[e];
            w[k] = ws[e];
            d[k] = ds[e];
        }
        return new Circuit(ids, regions, rowPtr, col, w, d);
    }

    /** A leaf child element: self-closing, or immediately closed with only whitespace/comments inside. */
    private void child(String name, Map<String, String> attrs) {
        if (!tag(name, attrs)) {
            skipContent();
            if (!s.startsWith("</" + name, pos)) {
                throw err("<" + name + "> must be empty");
            }
            pos += 2 + name.length();
            ws();
            expect('>');
        }
    }

    /** Parse "&lt;name attrs... &gt;" or "/&gt;". Returns true if self-closing. */
    private boolean tag(String name, Map<String, String> attrs) {
        expect('<');
        String got = name();
        if (!got.equals(name)) {
            throw err("expected <" + name + ">, found <" + got + ">");
        }
        while (true) {
            boolean hadWs = ws();
            if (pos >= s.length()) {
                throw err("unterminated <" + name);
            }
            char c = s.charAt(pos);
            if (c == '/') {
                pos++;
                expect('>');
                return true;
            }
            if (c == '>') {
                pos++;
                return false;
            }
            if (!hadWs) {
                throw err("expected whitespace before attribute");
            }
            String k = name();
            ws();
            expect('=');
            ws();
            if (pos >= s.length()) {
                throw err("missing attribute value");
            }
            char q = s.charAt(pos);
            if (q != '"' && q != '\'') {
                throw err("attribute '" + k + "' value must be quoted");
            }
            int end = s.indexOf(q, pos + 1);
            if (end < 0) {
                throw err("unterminated attribute '" + k + "'");
            }
            String raw = s.substring(pos + 1, end);
            if (raw.indexOf('<') >= 0) {
                throw err("'<' in attribute '" + k + "'");
            }
            if (attrs.put(k, decode(raw)) != null) {
                throw err("repeated attribute '" + k + "'");
            }
            pos = end + 1;
        }
    }

    private String name() {
        int start = pos;
        while (pos < s.length()) {
            char c = s.charAt(pos);
            if (Character.isLetterOrDigit(c) || c == '_' || c == '-' || c == '.' || c == ':') {
                pos++;
            } else {
                break;
            }
        }
        if (pos == start) {
            throw err("expected a name");
        }
        return s.substring(start, pos);
    }

    /** Whitespace, comments and PIs between elements; anything else that isn't a tag is an error. */
    private void skipContent() {
        while (pos < s.length()) {
            if (ws()) {
                continue;
            }
            if (s.startsWith("<!--", pos)) {
                comment();
            } else if (s.startsWith("<?", pos)) {
                pi();
            } else if (s.startsWith("<!", pos)) {
                throw err("DOCTYPE / CDATA / declarations are not allowed");
            } else if (s.charAt(pos) == '<') {
                return;
            } else {
                throw err("text content is not allowed");
            }
        }
    }

    /** Prolog / epilog: whitespace, comments, PIs (incl. the XML declaration). */
    private void misc() {
        while (pos < s.length()) {
            if (ws()) {
                continue;
            }
            if (s.startsWith("<!--", pos)) {
                comment();
            } else if (s.startsWith("<?", pos)) {
                pi();
            } else if (s.startsWith("<!", pos)) {
                throw err("DOCTYPE / declarations are not allowed");
            } else {
                return;
            }
        }
    }

    private void comment() {
        int end = s.indexOf("-->", pos + 4);
        if (end < 0) {
            throw err("unterminated comment");
        }
        pos = end + 3;
    }

    private void pi() {
        int end = s.indexOf("?>", pos + 2);
        if (end < 0) {
            throw err("unterminated processing instruction");
        }
        pos = end + 2;
    }

    private boolean ws() {
        int start = pos;
        while (pos < s.length()) {
            char c = s.charAt(pos);
            if (c == ' ' || c == '\t' || c == '\n' || c == '\r') {
                pos++;
            } else {
                break;
            }
        }
        return pos > start;
    }

    private void expect(char c) {
        if (pos >= s.length() || s.charAt(pos) != c) {
            throw err("expected '" + c + "'");
        }
        pos++;
    }

    private static String decode(String raw) {
        if (raw.indexOf('&') < 0) {
            return raw;
        }
        StringBuilder b = new StringBuilder();
        int i = 0;
        while (i < raw.length()) {
            char c = raw.charAt(i);
            if (c != '&') {
                b.append(c);
                i++;
                continue;
            }
            int semi = raw.indexOf(';', i);
            if (semi < 0) {
                throw new IllegalArgumentException("connectome: bad entity in '" + raw + "'");
            }
            String e = raw.substring(i + 1, semi);
            switch (e) {
                case "amp": b.append('&'); break;
                case "lt": b.append('<'); break;
                case "gt": b.append('>'); break;
                case "quot": b.append('"'); break;
                case "apos": b.append('\''); break;
                default:
                    int cp;
                    try {
                        if (e.startsWith("#x")) {
                            cp = Integer.parseInt(e.substring(2), 16);
                        } else if (e.startsWith("#")) {
                            cp = Integer.parseInt(e.substring(1));
                        } else {
                            throw new IllegalArgumentException("connectome: unknown entity &" + e + ";");
                        }
                    } catch (NumberFormatException ex) {
                        throw new IllegalArgumentException("connectome: bad character reference &" + e + ";");
                    }
                    b.appendCodePoint(cp);
            }
            i = semi + 1;
        }
        return b.toString();
    }

    private static void allow(Map<String, String> a, String where, String... names) {
        outer:
        for (String k : a.keySet()) {
            for (String n : names) {
                if (n.equals(k)) {
                    continue outer;
                }
            }
            throw new IllegalArgumentException(where + " has unknown attribute '" + k + "'");
        }
    }

    private static String required(Map<String, String> a, String name, String where) {
        String v = a.get(name);
        if (v == null) {
            throw new IllegalArgumentException(where + " is missing required attribute '" + name + "'");
        }
        return v;
    }

    /** Decimal number (xs:double lexical form, no INF/NaN). Rejects Java-only spellings like "1d" or "0x1p3". */
    private static double number(String raw, String attr, String where) {
        String t = raw.trim();
        if (!isDecimal(t)) {
            throw new IllegalArgumentException(where + " " + attr + " is not a number: '" + raw + "'");
        }
        double v = Double.parseDouble(t);
        if (Double.isNaN(v) || Double.isInfinite(v)) {
            throw new IllegalArgumentException(where + " " + attr + " must be finite, got '" + raw + "'");
        }
        return v;
    }

    /** [+-]? (digits [. digits*] | . digits) ([eE] [+-]? digits)? */
    static boolean isDecimal(String t) {
        int i = 0;
        int n = t.length();
        if (i < n && (t.charAt(i) == '+' || t.charAt(i) == '-')) {
            i++;
        }
        int intDigits = 0;
        while (i < n && t.charAt(i) >= '0' && t.charAt(i) <= '9') {
            i++;
            intDigits++;
        }
        int fracDigits = 0;
        if (i < n && t.charAt(i) == '.') {
            i++;
            while (i < n && t.charAt(i) >= '0' && t.charAt(i) <= '9') {
                i++;
                fracDigits++;
            }
        }
        if (intDigits + fracDigits == 0) {
            return false;
        }
        if (i < n && (t.charAt(i) == 'e' || t.charAt(i) == 'E')) {
            i++;
            if (i < n && (t.charAt(i) == '+' || t.charAt(i) == '-')) {
                i++;
            }
            int expDigits = 0;
            while (i < n && t.charAt(i) >= '0' && t.charAt(i) <= '9') {
                i++;
                expDigits++;
            }
            if (expDigits == 0) {
                return false;
            }
        }
        return i == n;
    }

    /**
     * Set of (pre, post) index pairs, open addressing on plain int arrays.
     * Replaces a HashSet&lt;Long&gt; keyed (pre &lt;&lt; 32 | post): Long.hashCode is
     * pre ^ post, which collides massively for local wiring (a 10k-neuron ring
     * with 20 out-synapses each has only 235 distinct hashes for 200k keys).
     * The JVM's HashMap treeifies such buckets; TeaVM's does not, so in the
     * browser every add walked a long chain of emulated-long equals: O(E^2).
     */
    static final class PairSet {
        private final int[] pre;
        private final int[] post;
        private final int mask;

        PairSet(int expected) {
            int cap = 16;
            while (cap < expected * 2) {
                cap <<= 1;
            }
            pre = new int[cap];
            post = new int[cap];
            mask = cap - 1;
            java.util.Arrays.fill(pre, -1);
        }

        /** Adds (a, b), both &gt;= 0; false if already present. */
        boolean add(int a, int b) {
            int h = a * 0x9E3779B1 + b;
            h ^= h >>> 16;
            h *= 0x85EBCA6B;
            h ^= h >>> 13;
            h *= 0xC2B2AE35;
            h ^= h >>> 16;
            int i = h & mask;
            while (pre[i] >= 0) {
                if (pre[i] == a && post[i] == b) {
                    return false;
                }
                i = (i + 1) & mask;
            }
            pre[i] = a;
            post[i] = b;
            return true;
        }
    }

    private IllegalArgumentException err(String msg) {
        int line = 1;
        for (int i = 0; i < Math.min(pos, s.length()); i++) {
            if (s.charAt(i) == '\n') {
                line++;
            }
        }
        return new IllegalArgumentException("connectome line " + line + ": " + msg);
    }
}
