// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT

package com.fruitfly.games.rhythm.client.llm;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class V3tCliTest {
    @Test
    void parsesSubcommands() {
        assertTrue(V3tCli.isV3tLine("/v3t hi"));
        assertFalse(V3tCli.isV3tLine("/v3tx"));
        assertFalse(LlmCli.isLlmLine("/v3t hi"));
        assertEquals(V3tCli.Kind.CHAT, V3tCli.parse("/v3t what is phi").kind);
        assertEquals("what is phi", V3tCli.parse("/v3t what is phi").arg);
        assertEquals(V3tCli.Kind.HISTORY, V3tCli.parse("/v3t history").kind);
        assertEquals("conv-1", V3tCli.parse("/v3t open conv-1").arg);
        assertEquals(V3tCli.Kind.HELP, V3tCli.parse("/v3t").kind);
    }

    @Test
    void tokenLinesAreSecretAndValidated() {
        assertTrue(V3tCli.isSecretLine("/v3t token cyt_abc"));
        assertFalse(V3tCli.isSecretLine("/v3t hello"));
        assertTrue(V3tCli.validToken("cyt_Ab-9_x"));
        assertFalse(V3tCli.validToken("cyt_a b"));
        assertFalse(V3tCli.validToken("abc"));
    }

    @Test
    void resolvesBaseLoopbackPagesAndOverride() {
        assertEquals(V3tCli.LOOPBACK_BASE, V3tCli.resolveBase("127.0.0.1", null));
        assertEquals(V3tCli.LOOPBACK_BASE, V3tCli.resolveBase("", null));
        assertEquals(V3tCli.PAGES_BASE, V3tCli.resolveBase("axiomiccoreness.github.io", null));
        assertEquals("https://x.example", V3tCli.resolveBase("axiomiccoreness.github.io", "https://x.example/"));
        assertEquals(V3tCli.PAGES_BASE, V3tCli.resolveBase("axiomiccoreness.github.io", "http://evil.example"));
        assertEquals(V3tCli.PAGES_BASE, V3tCli.resolveBase("axiomiccoreness.github.io", "http://0.0.0.0:8087"));
    }

    @Test
    void chatBodyEscapes() {
        assertEquals("{\"message\":\"a\\\"b\\nc\",\"max_tokens\":512,\"conversation_id\":\"c-1\"}",
                V3tCli.chatBody("a\"b\nc", "c-1"));
        assertEquals("{\"message\":\"x\",\"max_tokens\":512}", V3tCli.chatBody("x", "../bad"));
    }
}
