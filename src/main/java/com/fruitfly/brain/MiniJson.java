// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT

package com.fruitfly.brain;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Small JSON reader for the CB2514 classpath resources. JDK only.
 * Objects keep source key order.
 */
final class MiniJson {
    private final String text;
    private int index;

    private MiniJson(String text) {
        this.text = text;
    }

    static Object parse(String text) {
        if (text == null) {
            throw new IllegalArgumentException("json text must be non-null");
        }
        MiniJson parser = new MiniJson(text);
        Object value = parser.parseValue();
        parser.skipWhitespace();
        if (parser.index != text.length()) {
            throw new IllegalArgumentException("trailing junk at " + parser.index);
        }
        return value;
    }

    private Object parseValue() {
        skipWhitespace();
        if (index >= text.length()) {
            throw new IllegalArgumentException("unexpected end of json");
        }
        char c = text.charAt(index);
        if (c == '{') {
            return parseObject();
        }
        if (c == '[') {
            return parseArray();
        }
        if (c == '"') {
            return parseString();
        }
        if (c == 't' || c == 'f') {
            return parseBoolean();
        }
        if (c == 'n') {
            return parseNull();
        }
        if (c == '-' || (c >= '0' && c <= '9')) {
            return parseNumber();
        }
        throw new IllegalArgumentException("unexpected character at " + index);
    }

    private Map<String, Object> parseObject() {
        expect('{');
        Map<String, Object> object = new LinkedHashMap<>();
        skipWhitespace();
        if (peek('}')) {
            index++;
            return object;
        }
        while (true) {
            skipWhitespace();
            String key = parseString();
            skipWhitespace();
            expect(':');
            if (object.containsKey(key)) {
                throw new IllegalArgumentException("duplicate key: " + key);
            }
            object.put(key, parseValue());
            skipWhitespace();
            if (peek('}')) {
                index++;
                return object;
            }
            expect(',');
        }
    }

    private List<Object> parseArray() {
        expect('[');
        List<Object> values = new ArrayList<>();
        skipWhitespace();
        if (peek(']')) {
            index++;
            return values;
        }
        while (true) {
            values.add(parseValue());
            skipWhitespace();
            if (peek(']')) {
                index++;
                return values;
            }
            expect(',');
        }
    }

    private String parseString() {
        expect('"');
        StringBuilder out = new StringBuilder();
        while (index < text.length()) {
            char c = text.charAt(index++);
            if (c == '"') {
                return out.toString();
            }
            if (c == '\\') {
                if (index >= text.length()) {
                    throw new IllegalArgumentException("truncated escape");
                }
                char esc = text.charAt(index++);
                switch (esc) {
                    case '"':
                    case '\\':
                    case '/':
                        out.append(esc);
                        break;
                    case 'b':
                        out.append('\b');
                        break;
                    case 'f':
                        out.append('\f');
                        break;
                    case 'n':
                        out.append('\n');
                        break;
                    case 'r':
                        out.append('\r');
                        break;
                    case 't':
                        out.append('\t');
                        break;
                    case 'u':
                        if (index + 4 > text.length()) {
                            throw new IllegalArgumentException("truncated unicode escape");
                        }
                        int code = Integer.parseInt(text.substring(index, index + 4), 16);
                        out.append((char) code);
                        index += 4;
                        break;
                    default:
                        throw new IllegalArgumentException("bad escape at " + (index - 1));
                }
            } else if (c < 0x20) {
                throw new IllegalArgumentException("raw control character in string");
            } else {
                out.append(c);
            }
        }
        throw new IllegalArgumentException("unterminated string");
    }

    private Boolean parseBoolean() {
        if (text.startsWith("true", index)) {
            index += 4;
            return Boolean.TRUE;
        }
        if (text.startsWith("false", index)) {
            index += 5;
            return Boolean.FALSE;
        }
        throw new IllegalArgumentException("invalid boolean at " + index);
    }

    private Object parseNull() {
        if (text.startsWith("null", index)) {
            index += 4;
            return null;
        }
        throw new IllegalArgumentException("invalid null at " + index);
    }

    private Number parseNumber() {
        int start = index;
        if (peek('-')) {
            index++;
        }
        if (index >= text.length() || !digit(text.charAt(index))) {
            throw new IllegalArgumentException("invalid number at " + start);
        }
        if (text.charAt(index) == '0') {
            index++;
        } else {
            while (index < text.length() && digit(text.charAt(index))) {
                index++;
            }
        }
        boolean fractional = false;
        if (peek('.')) {
            fractional = true;
            index++;
            if (index >= text.length() || !digit(text.charAt(index))) {
                throw new IllegalArgumentException("invalid fraction at " + start);
            }
            while (index < text.length() && digit(text.charAt(index))) {
                index++;
            }
        }
        if (peek('e') || peek('E')) {
            fractional = true;
            index++;
            if (peek('+') || peek('-')) {
                index++;
            }
            if (index >= text.length() || !digit(text.charAt(index))) {
                throw new IllegalArgumentException("invalid exponent at " + start);
            }
            while (index < text.length() && digit(text.charAt(index))) {
                index++;
            }
        }
        String literal = text.substring(start, index);
        if (!fractional) {
            try {
                return Long.valueOf(literal);
            } catch (NumberFormatException e) {
                throw new IllegalArgumentException("integer out of range: " + literal);
            }
        }
        double value = Double.parseDouble(literal);
        if (!Double.isFinite(value)) {
            throw new IllegalArgumentException("non-finite number: " + literal);
        }
        return value;
    }

    private void skipWhitespace() {
        while (index < text.length()) {
            char c = text.charAt(index);
            if (c == ' ' || c == '\n' || c == '\r' || c == '\t') {
                index++;
            } else {
                return;
            }
        }
    }

    private boolean peek(char c) {
        return index < text.length() && text.charAt(index) == c;
    }

    private void expect(char c) {
        if (!peek(c)) {
            throw new IllegalArgumentException("expected '" + c + "' at " + index);
        }
        index++;
    }

    private static boolean digit(char c) {
        return c >= '0' && c <= '9';
    }
}
