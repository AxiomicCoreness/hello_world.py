package com.fruitfly.games.rhythm.logic;

import java.util.ArrayList;
import java.util.List;

/**
 * Euclidean rhythms E(k, n): k pulses spread as evenly as possible over n
 * steps, built with Bjorklund's algorithm in the sequence-grouping form
 * described by Toussaint ("The Euclidean Algorithm Generates Traditional
 * Musical Rhythms", 2005).
 *
 * Start with k groups "x" and n-k groups "."; while more than one remainder
 * group is left, append one remainder group to each leading group, and the
 * groups that were not paired become the new remainder. Concatenating the
 * groups gives the pattern.
 *
 * Rotation convention: {@link #pattern(int, int)} returns this canonical
 * Bjorklund output, which always starts with a pulse on step 0, e.g.
 * E(3,8) = x..x..x. and E(5,8) = x.xx.xx.. {@link #rotate(boolean[], int)}
 * with r &gt; 0 rotates LEFT by r steps: the result starts at step r of the
 * input (so rotate(E(3,8), 1) = ..x..x.x). A rotation r is taken mod n.
 */
public final class Euclid {
    public static final int MAX_STEPS = 64;

    private Euclid() {
    }

    /** Canonical E(k, n), true = pulse. 0 &lt;= k &lt;= n, 1 &lt;= n &lt;= {@link #MAX_STEPS}. */
    public static boolean[] pattern(int k, int n) {
        if (n < 1 || n > MAX_STEPS) {
            throw new IllegalArgumentException("steps out of range: " + n);
        }
        if (k < 0 || k > n) {
            throw new IllegalArgumentException("pulses out of range: " + k + " of " + n);
        }
        List<List<Boolean>> a = new ArrayList<>();
        List<List<Boolean>> b = new ArrayList<>();
        for (int i = 0; i < k; i++) {
            a.add(single(true));
        }
        for (int i = 0; i < n - k; i++) {
            b.add(single(false));
        }
        if (k == 0) {
            a = b;
            b = new ArrayList<>();
        }
        while (b.size() > 1) {
            int m = Math.min(a.size(), b.size());
            List<List<Boolean>> paired = new ArrayList<>(m);
            for (int i = 0; i < m; i++) {
                List<Boolean> g = new ArrayList<>(a.get(i));
                g.addAll(b.get(i));
                paired.add(g);
            }
            List<List<Boolean>> rest = new ArrayList<>(a.size() > m ? a.subList(m, a.size()) : b.subList(m, b.size()));
            a = paired;
            b = rest;
        }
        boolean[] out = new boolean[n];
        int at = 0;
        List<List<Boolean>> all = new ArrayList<>(a);
        all.addAll(b);
        for (List<Boolean> g : all) {
            for (Boolean v : g) {
                out[at++] = v;
            }
        }
        return out;
    }

    /**
     * The fold, stage by stage, for the docs: "[1][1][1][0][0][0][0][0]",
     * "[1,0][1,0][1,0][0][0]", "[1,0,0][1,0,0][1,0]", then the flat "10010010".
     */
    public static List<String> foldTrace(int k, int n) {
        pattern(k, n); // validates
        List<String> out = new ArrayList<>();
        List<List<Boolean>> a = new ArrayList<>();
        List<List<Boolean>> b = new ArrayList<>();
        for (int i = 0; i < k; i++) {
            a.add(single(true));
        }
        for (int i = 0; i < n - k; i++) {
            b.add(single(false));
        }
        out.add(groups(a, b));
        while (k > 0 && b.size() > 1) {
            int m = Math.min(a.size(), b.size());
            List<List<Boolean>> paired = new ArrayList<>(m);
            for (int i = 0; i < m; i++) {
                List<Boolean> g = new ArrayList<>(a.get(i));
                g.addAll(b.get(i));
                paired.add(g);
            }
            List<List<Boolean>> rest = new ArrayList<>(a.size() > m ? a.subList(m, a.size()) : b.subList(m, b.size()));
            a = paired;
            b = rest;
            out.add(groups(a, b));
        }
        out.add(toText(pattern(k, n)).replace('x', '1').replace('.', '0'));
        return out;
    }

    private static String groups(List<List<Boolean>> a, List<List<Boolean>> b) {
        StringBuilder sb = new StringBuilder();
        List<List<Boolean>> all = new ArrayList<>(a);
        all.addAll(b);
        for (List<Boolean> g : all) {
            sb.append('[');
            for (int i = 0; i < g.size(); i++) {
                sb.append(i > 0 ? "," : "").append(g.get(i) ? '1' : '0');
            }
            sb.append(']');
        }
        return sb.toString();
    }

    /** Onsets by the floor formula P_i = floor(i * n / k), i = 0..k-1 (equals Bjorklund up to rotation). */
    public static boolean[] floorPattern(int k, int n) {
        pattern(k, n); // validates
        boolean[] p = new boolean[n];
        for (int i = 0; i < k; i++) {
            p[(int) ((long) i * n / k)] = true;
        }
        return p;
    }

    /** Steps between consecutive onsets, wrapping from the last back to the first. */
    public static int[] gaps(boolean[] p) {
        int k = pulses(p);
        int[] out = new int[k];
        int first = -1;
        int prev = -1;
        int j = 0;
        for (int i = 0; i < p.length; i++) {
            if (p[i]) {
                if (prev >= 0) {
                    out[j++] = i - prev;
                } else {
                    first = i;
                }
                prev = i;
            }
        }
        if (k > 0) {
            out[j] = p.length - prev + first;
        }
        return out;
    }

    private static List<Boolean> single(boolean v) {
        List<Boolean> g = new ArrayList<>(1);
        g.add(v);
        return g;
    }

    /** Rotate left by r (r may be negative or &gt;= n). */
    public static boolean[] rotate(boolean[] p, int r) {
        int n = p.length;
        boolean[] out = new boolean[n];
        if (n == 0) {
            return out;
        }
        int s = ((r % n) + n) % n;
        for (int i = 0; i < n; i++) {
            out[i] = p[(i + s) % n];
        }
        return out;
    }

    /** "x" for a pulse, "." for a rest. */
    public static String toText(boolean[] p) {
        StringBuilder b = new StringBuilder(p.length);
        for (boolean v : p) {
            b.append(v ? 'x' : '.');
        }
        return b.toString();
    }

    /** Parse an x/. string (anything but 'x'/'X' is a rest). */
    public static boolean[] fromText(String s) {
        boolean[] p = new boolean[s.length()];
        for (int i = 0; i < p.length; i++) {
            p[i] = s.charAt(i) == 'x' || s.charAt(i) == 'X';
        }
        return p;
    }

    /** True if {@code a} equals some rotation of {@code b}. */
    public static boolean isRotationOf(boolean[] a, boolean[] b) {
        if (a.length != b.length) {
            return false;
        }
        for (int r = 0; r < Math.max(1, b.length); r++) {
            if (java.util.Arrays.equals(a, rotate(b, r))) {
                return true;
            }
        }
        return false;
    }

    public static int pulses(boolean[] p) {
        int c = 0;
        for (boolean v : p) {
            if (v) {
                c++;
            }
        }
        return c;
    }
}
