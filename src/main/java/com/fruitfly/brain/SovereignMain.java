package com.fruitfly.brain;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Locale;

/**
 * Command-line entry point for the fruitfly.brain package.
 *
 * Stdlib only. No SLF4J. Modes (at most one of --chat, --sim, --repl):
 *   --chat "text" [--q FLOAT] [--p FLOAT]   one reply, exit 0
 *   --sim [--steps INT] [--dt FLOAT]        headless run, one summary line, exit 0
 *   --repl                                  line commands on stdin, exit 0 at EOF/exit
 *   (no mode flag)                          short interactive demo
 *
 * Every mode accepts --connectome-file PATH to load the network from XML
 * via {@link ConnectomeLoader}; without it the synthetic
 * Connectome.random(8, 0.25, 20_260_720L) is used. Load progress goes to
 * stderr so --chat and --sim stdout stay the bare result line.
 *
 * --sim and the REPL's {@code step} drive every neuron with
 * {@link #DRIVE} = 0.5 per step, the same value the demo loop and
 * SovereignAutomaton.respond use.
 *
 * Exit codes: 0 ok, 2 bad argument, conflicting modes or unloadable
 * connectome file, 3 empty reply, 4 internal error.
 */
public final class SovereignMain {

    /** External drive per step for the demo, --sim and REPL step (matches respond()). */
    static final double DRIVE = 0.5;

    static final String USAGE =
            "usage: SovereignMain [--chat <text> | --sim | --repl] [--q <float>] [--p <float>]"
            + " [--steps <int>] [--dt <float>] [--no-demo] [--connectome-file <path>]";

    static final String REPL_HELP =
            "commands: chat <text> | step [n] | state | help | exit | quit";

    private static final class Args {
        String  chat   = null;
        boolean sim    = false;
        boolean repl   = false;
        double  q      = 0.0;
        double  p      = 0.0;
        int     steps  = 100;
        double  dt     = 1e-4;
        boolean noDemo = false;
        Path    connectomeFile = null;
    }

    public static void main(String[] args) {
        System.exit(run(args, System.in, System.out, System.err));
    }

    /**
     * Testable entry: parses args, runs the selected mode against the given
     * streams and returns the exit code. Never calls System.exit.
     */
    static int run(String[] args, InputStream in, PrintStream out, PrintStream err) {
        Args a;
        try {
            a = parse(args);
        } catch (IllegalArgumentException e) {
            err.println("bad argument: " + e.getMessage());
            err.println(USAGE);
            return 2;
        }

        boolean hasMode = a.chat != null || a.sim || a.repl;
        if (a.noDemo && !hasMode) {
            return 0;
        }

        Connectome connectome;
        try {
            connectome = buildConnectome(a, err);
        } catch (Exception e) {
            err.println("failed to load connectome: " + e.getMessage());
            return 2;
        }

        if (a.chat != null) {
            return runChatMode(a, connectome, out, err);
        }
        if (a.sim) {
            return runSimMode(a, connectome, out, err);
        }
        if (a.repl) {
            return runRepl(a, connectome, in, out, err);
        }
        runInteractiveMode(a, connectome, out);
        return 0;
    }

    private static Args parse(String[] argv) {
        Args a = new Args();
        for (int i = 0; i < argv.length; i++) {
            String token = argv[i];
            switch (token) {
                case "--chat":
                    a.chat = requireValue(argv, ++i, "--chat");
                    break;
                case "--sim":
                    a.sim = true;
                    break;
                case "--repl":
                    a.repl = true;
                    break;
                case "--q":
                    a.q = Double.parseDouble(requireValue(argv, ++i, "--q"));
                    break;
                case "--p":
                    a.p = Double.parseDouble(requireValue(argv, ++i, "--p"));
                    break;
                case "--steps":
                    a.steps = Integer.parseInt(requireValue(argv, ++i, "--steps"));
                    break;
                case "--dt":
                    a.dt = Double.parseDouble(requireValue(argv, ++i, "--dt"));
                    break;
                case "--no-demo":
                    a.noDemo = true;
                    break;
                case "--connectome-file":
                    a.connectomeFile = Paths.get(requireValue(argv, ++i, "--connectome-file"));
                    break;
                default:
                    throw new IllegalArgumentException("unknown token: " + token);
            }
        }
        int modes = (a.chat != null ? 1 : 0) + (a.sim ? 1 : 0) + (a.repl ? 1 : 0);
        if (modes > 1) {
            throw new IllegalArgumentException("--chat, --sim and --repl are mutually exclusive");
        }
        if (a.steps <= 0) throw new IllegalArgumentException("--steps must be > 0");
        if (a.dt <= 0)    throw new IllegalArgumentException("--dt must be > 0");
        return a;
    }

    private static String requireValue(String[] argv, int i, String opt) {
        if (i >= argv.length) {
            throw new IllegalArgumentException("missing value for " + opt);
        }
        return argv[i];
    }

    /** Loaded connectome if --connectome-file was given, else the synthetic fallback. */
    private static Connectome buildConnectome(Args a, PrintStream err) throws java.io.IOException {
        if (a.connectomeFile == null) {
            return Connectome.random(8, 0.25, 20_260_720L);
        }
        err.println("Loading connectome from: " + a.connectomeFile);
        Connectome c = ConnectomeLoader.loadFromXml(a.connectomeFile);
        err.println("Loaded " + c.neuronCount() + " neurons, "
                + c.synapseCount() + " synapses");
        return c;
    }

    private static int runChatMode(Args a, Connectome connectome, PrintStream out, PrintStream err) {
        if (a.chat.isEmpty()) {
            err.println("empty chat");
            return 2;
        }
        try {
            SovereignAutomaton automaton =
                    new SovereignAutomaton(connectome, connectome.neuronCount());
            String reply = automaton.respond(a.chat, a.q, a.p);
            if (reply == null || reply.isEmpty()) {
                err.println("empty reply from automaton");
                return 3;
            }
            out.println(reply);
            return 0;
        } catch (Exception e) {
            err.println(e.getClass().getSimpleName() + ": " + e.getMessage());
            return 4;
        }
    }

    /** Headless: --steps steps of --dt with drive {@link #DRIVE}, one summary line. */
    private static int runSimMode(Args a, Connectome connectome, PrintStream out, PrintStream err) {
        try {
            SovereignAutomaton automaton =
                    new SovereignAutomaton(connectome, connectome.neuronCount());
            for (int k = 0; k < a.steps; k++) {
                automaton.step(a.dt, DRIVE);
            }
            out.println(simSummary(a, automaton));
            return 0;
        } catch (Exception e) {
            err.println(e.getClass().getSimpleName() + ": " + e.getMessage());
            return 4;
        }
    }

    private static String simSummary(Args a, SovereignAutomaton automaton) {
        return String.format(Locale.ROOT,
                "sim steps=%d dt=%s t=%.6f state=%s neurons=%d synapses=%d mean_v=%.6f",
                a.steps, java.math.BigDecimal.valueOf(a.dt).stripTrailingZeros().toPlainString(),
                automaton.time(), automaton.state(),
                automaton.connectome().neuronCount(), automaton.connectome().synapseCount(),
                meanVoltage(automaton));
    }

    private static double meanVoltage(SovereignAutomaton automaton) {
        double sum = 0.0;
        for (LIFRK4 n : automaton.swarm()) {
            sum += n.voltage();
        }
        return automaton.swarm().isEmpty() ? 0.0 : sum / automaton.swarm().size();
    }

    private static String stateLine(SovereignAutomaton automaton) {
        return String.format(Locale.ROOT,
                "t=%.6f state=%s neurons=%d synapses=%d mean_v=%.6f",
                automaton.time(), automaton.state(),
                automaton.connectome().neuronCount(), automaton.connectome().synapseCount(),
                meanVoltage(automaton));
    }

    /**
     * Line REPL over the given streams. One automaton for the whole session.
     * chat uses --q/--p; step uses --dt and drive {@link #DRIVE}.
     * Returns 0 on exit/quit/EOF, 4 on an internal error.
     */
    static int runRepl(Args a, Connectome connectome, InputStream in, PrintStream out, PrintStream err) {
        SovereignAutomaton automaton;
        try {
            automaton = new SovereignAutomaton(connectome, connectome.neuronCount());
        } catch (Exception e) {
            err.println(e.getClass().getSimpleName() + ": " + e.getMessage());
            return 4;
        }
        out.println("SovereignMain REPL. " + REPL_HELP);
        BufferedReader reader = new BufferedReader(new InputStreamReader(in, StandardCharsets.UTF_8));
        try {
            while (true) {
                out.print("brain> ");
                out.flush();
                String raw = reader.readLine();
                if (raw == null) {
                    out.println();
                    return 0;
                }
                String line = raw.trim();
                if (line.isEmpty()) {
                    continue;
                }
                String[] parts = line.split("\\s+", 2);
                String cmd = parts[0];
                String arg = parts.length > 1 ? parts[1].trim() : "";
                switch (cmd) {
                    case "exit":
                    case "quit":
                        return 0;
                    case "help":
                        out.println(REPL_HELP);
                        break;
                    case "state":
                        out.println(stateLine(automaton));
                        break;
                    case "chat":
                        if (arg.isEmpty()) {
                            out.println("usage: chat <text>");
                        } else {
                            out.println(automaton.respond(arg, a.q, a.p));
                        }
                        break;
                    case "step": {
                        int n = 1;
                        if (!arg.isEmpty()) {
                            try {
                                n = Integer.parseInt(arg);
                            } catch (NumberFormatException e) {
                                n = 0;
                            }
                            if (n <= 0) {
                                out.println("step needs a positive integer, got: " + arg);
                                break;
                            }
                        }
                        for (int k = 0; k < n; k++) {
                            automaton.step(a.dt, DRIVE);
                        }
                        out.println(stateLine(automaton));
                        break;
                    }
                    default:
                        out.println("unknown command: " + cmd + " (type 'help')");
                }
            }
        } catch (IOException | RuntimeException e) {
            err.println(e.getClass().getSimpleName() + ": " + e.getMessage());
            return 4;
        }
    }

    private static void runInteractiveMode(Args a, Connectome connectome, PrintStream out) {
        out.println("Sovereign Brain starting — phi = " + SovereignConstants.PHI);

        out.println("Connectome: " + connectome.neuronCount()
                + " neurons, " + connectome.synapseCount() + " synapses");

        DarkStateInvariant dark = new DarkStateInvariant();
        out.println("Dark-state verify: " + dark.verify()
                + "  lambda2 = " + dark.lambda2()
                + "  residual = " + dark.eigenvalueResidual());

        SovereignAutomaton automaton =
                new SovereignAutomaton(connectome, connectome.neuronCount());
        for (int k = 0; k < a.steps; k++) {
            automaton.step(a.dt, DRIVE);
        }
        out.println("Simulation complete at t = " + automaton.time()
                + " s, state = " + automaton.state());

        int n = connectome.neuronCount();
        double[] voltages = new double[n];
        for (int i = 0; i < n; i++) {
            voltages[i] = automaton.swarm().get(i).voltage();
        }
        double[][] tensor = new double[n][n];
        GradientSynchronization.gradientSynchronizationPriority(voltages, tensor);
        out.println("Gradient sync applied with eta = " + SovereignConstants.ETA_UNITY);
        out.println("Sovereign Brain terminated");
    }

    private SovereignMain() {}
}
