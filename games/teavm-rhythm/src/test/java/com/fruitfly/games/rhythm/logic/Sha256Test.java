package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import org.junit.jupiter.api.Test;

/** The pure-Java SHA-256 used for the moves hash chain: FIPS 180-4 vectors and the JDK's MessageDigest. */
class Sha256Test {
    @Test
    void fipsVectors() {
        assertEquals("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", Sha256.hex(""));
        assertEquals("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", Sha256.hex("abc"));
        assertEquals("248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1",
            Sha256.hex("abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq"));
        StringBuilder m = new StringBuilder();
        for (int i = 0; i < 1_000_000; i++) {
            m.append('a');
        }
        assertEquals("cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0", Sha256.hex(m.toString()));
    }

    @Test
    void matchesMessageDigestOnEveryLengthAndUtf8() throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        StringBuilder s = new StringBuilder();
        for (int len = 0; len < 200; len++) {
            String x = s.toString();
            assertEquals(hex(md.digest(x.getBytes(StandardCharsets.UTF_8))), Sha256.hex(x), "len " + len);
            s.append((char) ('a' + len % 26));
            if (len % 37 == 5) {
                s.append("\u00b7\u266a\ud83e\udeb0"); // 2-, 3- and 4-byte UTF-8
            }
        }
    }

    static String hex(byte[] b) {
        StringBuilder r = new StringBuilder();
        for (byte x : b) {
            r.append(String.format("%02x", x & 0xff));
        }
        return r.toString();
    }
}
