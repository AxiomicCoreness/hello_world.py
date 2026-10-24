package com.fruitfly.games.rhythm.logic;

/** Tiny JSON writer helpers (no reflection; TeaVM-safe). */
public final class Json {
    private Json() {
    }

    /** Quoted, escaped JSON string; null becomes {@code null}. */
    public static String str(String s) {
        if (s == null) {
            return "null";
        }
        StringBuilder b = new StringBuilder(s.length() + 2);
        b.append('"');
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            switch (c) {
                case '"': b.append("\\\""); break;
                case '\\': b.append("\\\\"); break;
                case '\n': b.append("\\n"); break;
                case '\r': b.append("\\r"); break;
                case '\t': b.append("\\t"); break;
                default:
                    if (c < 0x20) {
                        String h = Integer.toHexString(c);
                        b.append("\\u");
                        for (int k = h.length(); k < 4; k++) {
                            b.append('0');
                        }
                        b.append(h);
                    } else {
                        b.append(c);
                    }
            }
        }
        return b.append('"').toString();
    }

    /** Number rounded to one decimal; non-finite becomes {@code null}. */
    public static String num1(double d) {
        if (Double.isNaN(d) || Double.isInfinite(d)) {
            return "null";
        }
        long tenths = Math.round(d * 10.0);
        boolean neg = tenths < 0;
        long a = Math.abs(tenths);
        return (neg ? "-" : "") + (a / 10) + "." + (a % 10);
    }
}
