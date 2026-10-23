package com.fruitfly.games.rhythm.irc;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.junit.jupiter.api.Test;

class IrcChatCliTest {
    @Test
    void defaultTargetIsAbjects6669() {
        IrcChatCli cli = new IrcChatCli();
        assertEquals("irc.abjects.net:6669", cli.target());
        assertTrue(cli.statusLine().contains("6669"));
        assertTrue(cli.lines().get(0).contains("6669"));
    }

    @Test
    void connectPlansStubWithoutLiveSocket() {
        IrcChatCli cli = new IrcChatCli();
        List<String> out = cli.handle("/connect");
        assertEquals(IrcBridgeClientStub.State.PLANNED, cli.bridge().state());
        assertTrue(out.stream().anyMatch(s -> s.contains("irc.abjects.net:6697")));
        assertTrue(out.stream().anyMatch(s -> s.contains("6669")));
        assertTrue(cli.statusLine().startsWith("PLANNED"));
    }

    @Test
    void sayBeforeConnectHintsConnect() {
        IrcChatCli cli = new IrcChatCli();
        List<String> out = cli.handle("hello");
        assertTrue(out.stream().anyMatch(s -> s.contains("not connected")));
    }

    @Test
    void sayAfterConnectLocalEchoOnly() {
        IrcChatCli cli = new IrcChatCli();
        cli.handle("/connect");
        List<String> out = cli.handle("hi channel");
        assertTrue(out.stream().anyMatch(s -> s.contains("local echo")));
        assertTrue(out.stream().anyMatch(s -> s.contains("not sent")));
    }

    @Test
    void mtlsAndDisconnect() {
        IrcChatCli cli = new IrcChatCli();
        List<String> mtls = cli.handle("/mtls");
        assertTrue(mtls.stream().anyMatch(s -> s.contains("irc.abjects.net")));
        cli.handle("/connect");
        cli.handle("/disconnect");
        assertEquals(IrcBridgeClientStub.State.IDLE, cli.bridge().state());
        assertTrue(cli.statusLine().startsWith("IDLE"));
    }

    @Test
    void clearKeepsBanner() {
        IrcChatCli cli = new IrcChatCli();
        cli.handle("/connect");
        cli.handle("/clear");
        assertFalse(cli.lines().isEmpty());
        assertTrue(cli.lines().get(0).contains("6669"));
        // clear does not reset bridge state
        assertEquals(IrcBridgeClientStub.State.PLANNED, cli.bridge().state());
    }

    @Test
    void emptyInputNoOp() {
        IrcChatCli cli = new IrcChatCli();
        int before = cli.lines().size();
        assertTrue(cli.handle("   ").isEmpty());
        assertEquals(before, cli.lines().size());
    }
}
