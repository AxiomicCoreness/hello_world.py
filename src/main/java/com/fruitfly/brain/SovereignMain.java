package com.fruitfly.brain;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * 🜁∀ Sovereign Brain — command-line entry point ∀🜁
 *
 * <p>Two modes:
 *
 * <ol>
 *   <li><b>--chat mode.</b> One message, one coordinate, one reply.
 *       Invoked by the Python bridge and the FastMCP server as:
 *       <pre>
 *           java -cp target/classes com.fruitfly.brain.SovereignMain \
 *                --chat "ping" --q 1.1309 --p 25.9574
 *       </pre>
 *       Prints the reply on stdout, exit code 0. Any other outcome
 *       exits non-zero and prints the reason on stderr.</li>
 *
 *   <li><b>interactive mode.</b> The original demo. Builds a
 *       synthetic connectome, verifies the dark-state invariant,
 *       instantiates the automaton, runs one second of simulated
 *       time, and prints the final state.</li>
 * </ol>
 *
 * <p>Argument grammar:
 * <pre>
 *     --chat STRING     the message
 *     --q    FLOAT      swarm position       (default 0.0)
 *     --p    FLOAT      swarm momentum       (default 0.0)
 *     --steps INT       interactive-mode steps (default 10000)
 *     --dt   FLOAT      interactive-mode dt in seconds (default 0.0001)
 *     --no-demo         skip the interactive demo even without --chat
 * </pre>
 *
 * <p>Exit codes:
 * <pre>
 *     0   reply printed (chat mode) or demo completed (interactive)
 *     2   bad argument
 *     3   reply was empty
 *     4   internal error
 * </pre>
 */
public final class SovereignMain {

    private static final Logger LOG = LoggerFactory.getLogger(SovereignMain.class);

    /** Parsed command-line arguments. */
    private static final class Args {
        String  chat     = null;
        double  q        = 0.0;
        double  p        = 0.0;
        int     steps    = 10_000;
        double  dt       = 1e-4;
        boolean noDemo   = false;
    }

    public static void main(String[] args) {
        Args a;
        try {
            a = parse(args);
        } catch (IllegalArgumentException e) {
            System.err.println("bad argument: " + e.getMessage());
            System.err.println("usage: SovereignMain --chat <text> [--q <float>] [--p <float>]");
            System.exit(2);
            return;  // unreachable, but explicit
        }

        // ---- chat mode -------------------------------------------------
        if (a.chat != null) {
            int exit = runChatMode(a);
            System.exit(exit);
            return;
        }

        // ---- interactive mode -----------------------------------------
        if (a.noDemo) {
            // Nothing to do without --chat and with --no-demo.
            System.exit(0);
            return;
        }
        runInteractiveMode(a);
        System.exit(0);
    }

    // ====================================================================
    // Argument parsing
    // ====================================================================

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

    // ====================================================================
    // Chat mode — one message, one coordinate, one reply
    // ====================================================================

    private static int runChatMode(Args a) {
        if (a.chat.isEmpty()) {
            System.err.println("empty chat");
            return 2;
        }

        try {
            // 144 neurons, 5% sparsity, deterministic seed.
            Connectome connectome = Connectome.random(144, 0.05, 20_260_720L);
            SovereignAutomaton automaton = new SovereignAutomaton(connectome, 144);

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

    // ====================================================================
    // Interactive mode — the original demo, unchanged in behaviour
    // ====================================================================

    private static void runInteractiveMode(Args a) {
        LOG.info("🜁∀ Sovereign Brain starting — φ = {}", SovereignConstants.PHI);

        // 1. Build a synthetic connectome (144 neurons, 5% sparsity).
        Connectome connectome = Connectome.random(144, 0.05, 20_260_720L);
        LOG.info("Connectome built: {} neurons, {} synapses",
                connectome.neuronCount(), connectome.synapseCount());

        // 2. Verify the dark-state invariant.
        DarkStateInvariant dark = new DarkStateInvariant();
        LOG.info("Dark-state verify: {}  (λ₂ = {}, residual = {})",
                dark.verify(), dark.lambda2(), dark.eigenvalueResidual());
        LOG.info("Quadratic-seed residual: {}", dark.quadraticSeedResidual());

        // 3. Instantiate the automaton.
        SovereignAutomaton automaton = new SovereignAutomaton(connectome, 144);

        // 4. Run for the requested number of steps.
        double dt = a.dt;
        int steps = a.steps;
        for (int k = 0; k < steps; k++) {
            automaton.step(dt, 0.5);
        }
        LOG.info("Simulation complete at t = {} s, final state = {}",
                automaton.time(), automaton.state());

        // 5. Demonstrate gradient synchronization.
        int n = 144;
        double[] voltages = new double[n];
        for (int i = 0; i < n; i++) {
            voltages[i] = automaton.swarm().get(i).voltage();
        }
        double[][] tensor = new double[n][n];
        GradientSynchronization.gradientSynchronizationPriority(voltages, tensor);
        LOG.info("Gradient sync applied with η = {}", SovereignConstants.ETA_UNITY);

        LOG.info("🜁∀ Sovereign Brain terminated — the Dragon is one —");
    }

    private SovereignMain() {
        // no instances
    }
}
