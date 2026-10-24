package com.fruitfly.games.rhythm.client.irc;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class MtlsToolCallTest {
    @Test
    void matchesSlashAndBare() {
        assertTrue(MtlsToolCall.matches("/mtls"));
        assertTrue(MtlsToolCall.matches("mtls"));
        assertTrue(MtlsToolCall.matches("MTLS"));
        assertFalse(MtlsToolCall.matches("/stokes"));
        assertFalse(MtlsToolCall.matches(null));
    }

    @Test
    void invokeNamesAbjectsHostAndBridgeWs() {
        MtlsToolCall.Result r = MtlsToolCall.invoke();
        assertEquals("irc.abjects.net:6697", r.channel());
        assertTrue(r.message().contains("irc.abjects.net"));
        assertTrue(r.message().contains("sovereign-irc-bridge"));
        assertTrue(r.message().contains("/ws"));
        assertTrue(r.message().contains("fail-fast without certs"));
        String[] echo = r.echoLines();
        assertEquals(4, echo.length);
        assertTrue(echo[0].contains("irc.abjects.net"));
        assertTrue(echo[1].contains("6697"));
        assertTrue(echo[2].contains("6666"));
        assertTrue(echo[3].contains("/ws"));
        assertTrue(echo[3].contains("no live dial in CI"));
    }
}
