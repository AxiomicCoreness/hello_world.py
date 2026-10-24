package com.fruitfly.games.rhythm.client.ide;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;
import org.junit.jupiter.api.Test;

class PythonIdeCliTest {
    @Test
    void detectsIdeVerbs() {
        assertTrue(PythonIdeCli.isIdeLine("/py help"));
        assertTrue(PythonIdeCli.isIdeLine("py list"));
        assertTrue(PythonIdeCli.isIdeLine("/ide pointer"));
        assertTrue(PythonIdeCli.isIdeLine("ide"));
        assertFalse(PythonIdeCli.isIdeLine("hello"));
        assertFalse(PythonIdeCli.isIdeLine("/connect"));
    }

    @Test
    void stripVerb() {
        assertEquals("help", PythonIdeCli.stripVerb("/py help"));
        assertEquals("call golden_ratio", PythonIdeCli.stripVerb("py call golden_ratio"));
        assertEquals("", PythonIdeCli.stripVerb("/ide"));
    }

    @Test
    void fiftyFourCapabilities() {
        assertEquals(54, PythonIdeCli.CAPABILITIES.length);
        assertTrue(PythonIdeCli.known("golden_ratio"));
        assertTrue(PythonIdeCli.known("health"));
        assertFalse(PythonIdeCli.known("no_such_cap"));
    }

    @Test
    void helpAndListOffline() {
        List<String> help = PythonIdeCli.handleOffline("/py help");
        assertTrue(help.stream().anyMatch(s -> s.contains("pythonIDE")));
        List<String> list = PythonIdeCli.handleOffline("/py list");
        assertTrue(list.stream().anyMatch(s -> s.contains("golden_ratio")));
        assertTrue(list.stream().anyMatch(s -> s.startsWith("[Engine]")));
    }

    @Test
    void unknownCallYieldsTraceback() {
        List<String> lines = PythonIdeCli.handleOffline("/py call no_such_cap");
        assertTrue(lines.stream().anyMatch(s -> s.startsWith("[Traceback]")));
        assertTrue(lines.stream().anyMatch(s -> s.contains("CapabilityError") || s.contains("unknown capability")));
    }

    @Test
    void pointerMentions2300() {
        List<String> lines = PythonIdeCli.handleOffline("/py pointer");
        assertTrue(lines.stream().anyMatch(s -> s.contains("2300")));
        assertTrue(lines.stream().anyMatch(s -> s.contains("314")));
    }

    @Test
    void formatTracebackShape() {
        List<String> tb = PythonIdeCli.formatTraceback("mod.py", "ValueError", "boom", "hint");
        assertTrue(tb.get(0).contains("Traceback (most recent call last)"));
        assertTrue(tb.stream().anyMatch(s -> s.contains("ValueError: boom")));
        assertTrue(tb.stream().anyMatch(s -> s.contains("hint")));
    }

    @Test
    void deepinferOfflineSurfacesStub() {
        assertTrue(PythonIdeCli.isIdeLine("/py deepinfer"));
        assertTrue(PythonIdeCli.isIdeLine("/deepinfer"));
        List<String> lines = PythonIdeCli.handleOffline("/py deepinfer");
        assertTrue(lines.stream().anyMatch(s -> s.toLowerCase().contains("deepinfer")));
    }

    @Test
    void katexOfflineSurfacesStub() {
        assertTrue(PythonIdeCli.isIdeLine("/py katex"));
        assertTrue(PythonIdeCli.isIdeLine("/katex"));
        List<String> lines = PythonIdeCli.handleOffline("/py katex");
        assertTrue(lines.stream().anyMatch(s -> s.contains("KaTeXMacroSetTest") || s.toLowerCase().contains("katex")));
    }
}
