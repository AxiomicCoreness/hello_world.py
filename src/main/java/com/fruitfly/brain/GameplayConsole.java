package com.fruitfly.brain;

import java.util.Scanner;

/**
 * 🜁∀ GameplayConsole — Sovereign Brain Console
 * Fruitfly brain (Drosophila) + AKLT dark-state invariant.
 * No SLF4J, no Maven. Compiled with javac against SovereignConstants
 * and DarkStateInvariant.
 *
 * Commands: status, step, dark, verify, help, exit
 * Phase ordinal is the turn. DARK_STATE is absorbing. verify() gates advance.
 *
 * Seal: ∀∞φ² · GAMEPLAY_CONSOLE · WOOD_DRAGON_0.91 · SEALED
 */
public final class GameplayConsole {

    private static final double PHI = 1.618033988749895;
    private static final double PHI_INV = 1.0 / PHI;
    private static final double NULL_BAN = 10.06;

    private final SovereignConstants constants;
    private final DarkStateInvariant darkState;

    private int turn = 0;
    private boolean absorbing = false;
    private String phase;

    public GameplayConsole() {
        this.constants = new SovereignConstants();
        this.darkState = new DarkStateInvariant();
        this.phase = Phase.OBSERVATION.name();
    }

    // ── Phase ordinal (turn) ─────────────────────────────────────────
    enum Phase {
        OBSERVATION,
        RESONANCE,
        HARMONIZATION,
        SYNTHESIS,
        INTEGRATION,
        PERPETUATION,
        TRANSCENDENCE
    }

    // ── Main loop ────────────────────────────────────────────────────
    public void run() {
        System.out.printf("φ = %.15f  λ₂ = %.1f  seed residual = %.3e%n",
                PHI, darkState.lambda2(), darkState.seedResidual());
        Scanner in = new Scanner(System.in);
        while (!absorbing) {
            printPrompt();
            if (!in.hasNextLine()) break;
            String cmd = in.nextLine().trim().toLowerCase();
            switch (cmd) {
                case "status": status(); break;
                case "step":   step();   break;
                case "dark":   dark();   break;
                case "verify": verify(); break;
                case "help":   help();   break;
                case "exit":   return;
                default:       System.out.println("unknown command. try 'help'.");
            }
        }
        System.out.println("DARK_STATE absorbed. Console exiting.");
    }

    private void printPrompt() {
        System.out.printf("phase %d/%d  %s  absorbing=%b%n> ",
                turn, Phase.values().length - 1, phase, absorbing);
    }

    private void status() {
        System.out.printf("turn=%d  phase=%s  absorbing=%b%n",
                turn, phase, absorbing);
    }

    private void step() {
        if (!verify()) {
            System.out.println("verify() failed — cannot advance.");
            return;
        }
        turn++;
        int ordinal = Math.min(turn, Phase.values().length - 1);
        phase = Phase.values()[ordinal].name();
        System.out.printf("advanced → %s%n", phase);
    }

    private void dark() {
        absorbing = true;
        phase = "DARK_STATE";
        System.out.println("DARK_STATE engaged — absorbing terminal.");
    }

    private void verify() {
        boolean ok = verifyInternal();
        System.out.printf("verify=%b  residual=%.3e  seed=%.3e%n",
                ok, darkState.residual(), darkState.seedResidual());
    }

    private boolean verifyInternal() {
        // Gate: residual must be below φ⁻¹⁰⁰⁰, seed below 1e-12
        double tol = Math.pow(PHI_INV, 1000);
        return darkState.residual() < tol
            && darkState.seedResidual() < 1e-12
            && darkState.lambda2() == 1.0;
    }

    private void help() {
        System.out.println("commands: status | step | dark | verify | help | exit");
    }

    public static void main(String[] args) {
        new GameplayConsole().run();
    }
}
