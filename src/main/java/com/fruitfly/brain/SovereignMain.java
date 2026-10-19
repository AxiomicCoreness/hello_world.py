package com.fruitfly.brain;

import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * Command-line entry point for the fruitfly.brain package.
 *
 * Stdlib only. No SLF4J. Two modes:
 *   --chat "text" [--q FLOAT] [--p FLOAT]   one reply, exit 0
 *   (no args)                               short interactive demo
 *
 * Both modes accept --connectome-file PATH to load the network from XML
 * via {@link ConnectomeLoader}; without it the synthetic
 * Connectome.random(8, 0.25, 20_260_720L) is used. Load progress goes to
 * stderr so --chat stdout stays the bare reply.
 *
 * Exit codes: 0 ok, 2 bad argument or unloadable connectome file,
 * 3 empty reply, 4 internal error.
 */
public final class SovereignMain {

    private static final class Args {
        String  chat   = null;
        double  q      = 0.0;
        double  p      = 0.0;
        int     steps  = 100;
        double  dt     = 1e-4;
        boolean noDemo = false;
        Path    connectomeFile = null;
    }

    public static void main(String[] args) {
        Args a;
        try {
            a = parse(args);
        } catch (IllegalArgumentException e) {
            System.err.println("bad argument: " + e.getMessage());
            System.err.println("usage: SovereignMain [--chat <text>] [--q <float>] [--p <float>]"
                    + " [--steps <int>] [--dt <float>] [--no-demo] [--connectome-file <path>]");
            System.exit(2);
            return;
        }

        if (a.noDemo && a.chat == null) {
            System.exit(0);
            return;
        }

        Connectome connectome;
        try {
            connectome = buildConnectome(a);
        } catch (Exception e) {
            System.err.println("failed to load connectome: " + e.getMessage());
            System.exit(2);
            return;
        }

        if (a.chat != null) {
            System.exit(runChatMode(a, connectome));
            return;
        }
        runInteractiveMode(a, connectome);
        System.exit(0);
    }

    private static Args parse(String[] argv) {
        Args a = new Args();
        for (int i = 0; i < argv.length; i++) {
            String token = argv[i];
            switch (token) {
                case "--chat":
                    a.chat = requireValue(argv, ++i, "--chat");
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
    private static Connectome buildConnectome(Args a) throws java.io.IOException {
        if (a.connectomeFile == null) {
            return Connectome.random(8, 0.25, 20_260_720L);
        }
        System.err.println("Loading connectome from: " + a.connectomeFile);
        Connectome c = ConnectomeLoader.loadFromXml(a.connectomeFile);
        System.err.println("Loaded " + c.neuronCount() + " neurons, "
                + c.synapseCount() + " synapses");
        return c;
    }

    private static int runChatMode(Args a, Connectome connectome) {
        if (a.chat.isEmpty()) {
            System.err.println("empty chat");
            return 2;
        }
        try {
            SovereignAutomaton automaton =
                    new SovereignAutomaton(connectome, connectome.neuronCount());
            String reply = automaton.respond(a.chat, a.q, a.p);
            if (reply == null || reply.isEmpty()) {
                System.err.println("empty reply from automaton");
                return 3;
            }
            System.out.println(reply);
            return 0;
        } catch (Exception e) {
            System.err.println(e.getClass().getSimpleName() + ": " + e.getMessage());
            return 4;
        }
    }

    private static void runInteractiveMode(Args a, Connectome connectome) {
        System.out.println("Sovereign Brain starting — phi = " + SovereignConstants.PHI);

        System.out.println("Connectome: " + connectome.neuronCount()
                + " neurons, " + connectome.synapseCount() + " synapses");

        DarkStateInvariant dark = new DarkStateInvariant();
        System.out.println("Dark-state verify: " + dark.verify()
                + "  lambda2 = " + dark.lambda2()
                + "  residual = " + dark.eigenvalueResidual());

        SovereignAutomaton automaton =
                new SovereignAutomaton(connectome, connectome.neuronCount());
        for (int k = 0; k < a.steps; k++) {
            automaton.step(a.dt, 0.5);
        }
        System.out.println("Simulation complete at t = " + automaton.time()
                + " s, state = " + automaton.state());

        int n = connectome.neuronCount();
        double[] voltages = new double[n];
        for (int i = 0; i < n; i++) {
            voltages[i] = automaton.swarm().get(i).voltage();
        }
        double[][] tensor = new double[n][n];
        GradientSynchronization.gradientSynchronizationPriority(voltages, tensor);
        System.out.println("Gradient sync applied with eta = " + SovereignConstants.ETA_UNITY);
        System.out.println("Sovereign Brain terminated");
    }

    private SovereignMain() {}
}
