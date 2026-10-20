package com.fruitfly.brain;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;

import org.junit.jupiter.api.Test;

/** SovereignMain.run with injected streams: --sim, --repl, mode conflicts, existing flags. */
class SovereignMainTest {

    private static final String PLACEHOLDER = "src/main/resources/HHMIJaneliaMap.xml";

    private static final class Result {
        final int code;
        final String out;
        final String err;
        Result(int code, String out, String err) {
            this.code = code;
            this.out = out;
            this.err = err;
        }
    }

    private static Result withStdin(String stdin, String... args) {
        InputStream in = new ByteArrayInputStream(stdin.getBytes(StandardCharsets.UTF_8));
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        ByteArrayOutputStream err = new ByteArrayOutputStream();
        int code = SovereignMain.run(args, in,
                new PrintStream(out, true, StandardCharsets.UTF_8),
                new PrintStream(err, true, StandardCharsets.UTF_8));
        return new Result(code,
                out.toString(StandardCharsets.UTF_8),
                err.toString(StandardCharsets.UTF_8));
    }

    private static Result run(String... args) {
        return withStdin("", args);
    }

    // ---- --sim ----

    @Test
    void simDefaultPrintsOneSummaryLine() {
        Result r = run("--sim");
        assertEquals(0, r.code, r.err);
        String[] lines = r.out.split("\\R");
        assertEquals(1, lines.length, r.out);
        assertTrue(lines[0].matches(
                "sim steps=100 dt=0\\.0001 t=0\\.010000 state=DARK_STATE"
                + " neurons=8 synapses=13 mean_v=-?\\d+\\.\\d{6}"), lines[0]);
    }

    @Test
    void simIsDeterministic() {
        Result a = run("--sim", "--steps", "37", "--dt", "0.001");
        Result b = run("--sim", "--steps", "37", "--dt", "0.001");
        assertEquals(0, a.code);
        assertEquals(a.out, b.out);
        assertTrue(a.out.startsWith("sim steps=37 dt=0.001 t=0.037000 "), a.out);
    }

    @Test
    void simFewStepsStopsBeforeDarkState() {
        Result r = run("--sim", "--steps", "3");
        assertEquals(0, r.code);
        assertTrue(r.out.contains("t=0.000300 state=SYNTHESIS "), r.out);
    }

    @Test
    void simUsesLoadedConnectome() {
        Result r = run("--sim", "--steps", "5", "--connectome-file", PLACEHOLDER);
        assertEquals(0, r.code, r.err);
        assertTrue(r.out.contains(" neurons=3 synapses=3 "), r.out);
        assertTrue(r.err.contains("Loaded 3 neurons"), r.err);
        assertFalse(r.out.contains("Loading"), "load progress must stay on stderr");
    }

    @Test
    void simBadStepsOrDtExits2() {
        for (String[] args : new String[][] {
                {"--sim", "--steps", "0"},
                {"--sim", "--steps", "-4"},
                {"--sim", "--steps", "abc"},
                {"--sim", "--steps"},
                {"--sim", "--dt", "0"},
                {"--sim", "--dt", "-1e-4"},
                {"--sim", "--dt", "nope"},
        }) {
            Result r = run(args);
            assertEquals(2, r.code, String.join(" ", args));
            assertEquals("", r.out);
            assertTrue(r.err.contains("usage: SovereignMain"), r.err);
        }
    }

    @Test
    void simMissingConnectomeExits2() {
        Result r = run("--sim", "--connectome-file", "does/not/exist.xml");
        assertEquals(2, r.code);
        assertTrue(r.err.contains("failed to load connectome"), r.err);
    }

    // ---- mode conflicts ----

    @Test
    void combinedModesExit2WithUsage() {
        for (String[] args : new String[][] {
                {"--chat", "hi", "--sim"},
                {"--sim", "--repl"},
                {"--repl", "--chat", "hi"},
                {"--chat", "hi", "--sim", "--repl"},
        }) {
            Result r = run(args);
            assertEquals(2, r.code, String.join(" ", args));
            assertTrue(r.err.contains("mutually exclusive"), r.err);
            assertTrue(r.err.contains("usage: SovereignMain"), r.err);
            assertEquals("", r.out);
        }
    }

    // ---- --repl ----

    @Test
    void replCommandsAndExit() {
        Result r = withStdin("help\nstate\nstep\nstep 2\nchat hello\nexit\nstate\n", "--repl");
        assertEquals(0, r.code, r.err);
        assertTrue(r.out.contains(SovereignMain.REPL_HELP), r.out);
        assertTrue(r.out.contains("t=0.000000 state=OBSERVATION neurons=8 synapses=13"), r.out);
        assertTrue(r.out.contains("t=0.000100 state="), r.out);
        assertTrue(r.out.contains("t=0.000300 state="), r.out);
        assertTrue(r.out.contains("phase="), r.out);
        assertTrue(r.out.contains("t=0.000400"), "chat advances one step: " + r.out);
        // nothing after exit runs: OBSERVATION appears only once
        assertEquals(r.out.indexOf("state=OBSERVATION"), r.out.lastIndexOf("state=OBSERVATION"));
    }

    @Test
    void replQuitAlsoExits() {
        Result r = withStdin("quit\nstep\n", "--repl");
        assertEquals(0, r.code);
        assertFalse(r.out.contains("t=0.000100"), r.out);
    }

    @Test
    void replEofExits0() {
        Result r = withStdin("state\n", "--repl");
        assertEquals(0, r.code);
        assertTrue(r.out.contains("state=OBSERVATION"), r.out);
        assertEquals(0, withStdin("", "--repl").code);
    }

    @Test
    void replUnknownCommandContinues() {
        Result r = withStdin("dance\nstep\n", "--repl");
        assertEquals(0, r.code);
        assertTrue(r.out.contains("unknown command: dance"), r.out);
        assertTrue(r.out.contains("t=0.000100"), "kept going after unknown command: " + r.out);
    }

    @Test
    void replBadStepArgAndEmptyChatContinue() {
        Result r = withStdin("step x\nstep 0\nchat\nstate\n", "--repl");
        assertEquals(0, r.code);
        assertTrue(r.out.contains("step needs a positive integer, got: x"), r.out);
        assertTrue(r.out.contains("step needs a positive integer, got: 0"), r.out);
        assertTrue(r.out.contains("usage: chat <text>"), r.out);
        assertTrue(r.out.contains("t=0.000000 state=OBSERVATION"), r.out);
    }

    @Test
    void replUsesDtAndQp() {
        Result r = withStdin("step 4\nchat hi\n", "--repl", "--dt", "0.01", "--q", "1.5", "--p", "2");
        assertEquals(0, r.code);
        assertTrue(r.out.contains("t=0.040000 "), r.out);
        assertTrue(r.out.contains("q=1.5000 p=2.0000 t=0.040100"), r.out);
    }

    @Test
    void replWithLoadedConnectome() {
        Result r = withStdin("state\n", "--repl", "--connectome-file", PLACEHOLDER);
        assertEquals(0, r.code, r.err);
        assertTrue(r.out.contains("neurons=3 synapses=3"), r.out);
    }

    // ---- existing behaviour kept ----

    @Test
    void chatUnchanged() {
        Result r = run("--chat", "hello", "--q", "1.13", "--p", "25.96");
        assertEquals(0, r.code);
        assertEquals("phase=RESONANCE q=1.1300 p=25.9600 t=0.000100" + System.lineSeparator(), r.out);
    }

    @Test
    void existingExitCodesUnchanged() {
        assertEquals(2, run("--chat", "").code);
        assertEquals(2, run("--foo").code);
        assertEquals(2, run("--chat").code);
        assertEquals(2, run("--steps", "x").code);
        assertEquals(2, run("--chat", "hi", "--connectome-file", "nope.xml").code);
        Result nd = run("--no-demo");
        assertEquals(0, nd.code);
        assertEquals("", nd.out);
    }

    @Test
    void defaultDemoUnchanged() {
        Result r = run("--steps", "3");
        assertEquals(0, r.code);
        String nl = System.lineSeparator();
        assertEquals("Sovereign Brain starting — phi = 1.618033988749895" + nl
                + "Connectome: 8 neurons, 13 synapses" + nl
                + "Dark-state verify: true  lambda2 = 1.0  residual = 0.0" + nl
                + "Simulation complete at t = 3.0000000000000003E-4 s, state = SYNTHESIS" + nl
                + "Gradient sync applied with eta = 1.0" + nl
                + "Sovereign Brain terminated" + nl, r.out);
    }
}
