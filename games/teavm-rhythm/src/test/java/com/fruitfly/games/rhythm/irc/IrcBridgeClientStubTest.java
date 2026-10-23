package com.fruitfly.games.rhythm.irc;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

class IrcBridgeClientStubTest {
    @Test
    void planDialDoesNotOpenSocketsAndNamesHost() {
        IrcBridgeClientStub c = new IrcBridgeClientStub();
        assertEquals(IrcBridgeClientStub.State.IDLE, c.state());
        String plan = c.planDial();
        assertEquals(IrcBridgeClientStub.State.PLANNED, c.state());
        assertTrue(plan.contains("irc.abjects.net:6697"));
        assertTrue(plan.contains("/ws"));
        assertTrue(plan.contains("IRC__MTLS_CERT_PATH"));
        assertEquals(plan, c.lastPlan());
    }

    @Test
    void toolCallMtlsDelegates() {
        MtlsToolCall.Result r = new IrcBridgeClientStub().toolCall("/mtls");
        assertEquals("irc.abjects.net:6697", r.channel());
    }

    @Test
    void unknownToolRejected() {
        assertThrows(IllegalArgumentException.class,
            () -> new IrcBridgeClientStub().toolCall("/stokes"));
    }

    @Test
    void configUiEndpoints() {
        assertEquals("irc.abjects.net:6666", IrcBridgeConfig.uiEndpoint(0));
        assertEquals("irc.abjects.net:6669", IrcBridgeConfig.uiEndpoint(3));
        assertEquals("irc.abjects.net:6666", IrcBridgeConfig.uiEndpoint(4));
    }

    @Test
    void resetReturnsToIdle() {
        IrcBridgeClientStub c = new IrcBridgeClientStub();
        c.planDial();
        c.reset();
        assertEquals(IrcBridgeClientStub.State.IDLE, c.state());
        assertEquals(null, c.lastPlan());
    }
}
