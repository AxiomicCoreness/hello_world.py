package com.fruitfly.brain;

import java.util.Scanner;

/**
 * Interactive console for the fruitfly.brain package.
 *
 * Stdlib only. Uses DarkStateInvariant.verify and SovereigntyState.
 * Commands: status, step, dark, verify, help, exit
 */
public final class GameplayConsole {

    private final DarkStateInvariant darkState;
    private int turn = 0;
    private boolean absorbing = false;
    private SovereigntyState phase = SovereigntyState.OBSERVATION;

    public GameplayConsole() {
        this.darkState = new DarkStateInvariant();
    }

    public void run() {
        System.out.printf("phi = %.15f  lambda2 = %.1f  seed = %.3e%n",
                SovereignConstants.PHI, darkState.lambda2(), darkState.quadraticSeedResidual());
        Scanner in = new Scanner(System.in);
        while (!absorbing) {
            printPrompt();
            if (!in.hasNextLine()) break;
            String cmd = in.nextLine().trim().toLowerCase();
            switch (cmd) {
                case "status": status(); break;
                case "step":   step();   break;
                case "dark":   dark();   break;
                case "verify": printVerify(); break;
                case "help":   help();   break;
                case "exit":   return;
                default:       System.out.println("unknown command. try 'help'.");
            }
        }
        System.out.println("DARK_STATE absorbed. Console exiting.");
    }

    private void printPrompt() {
        System.out.printf("phase %d  %s  absorbing=%b%n> ",
                turn, phase, absorbing);
    }

    private void status() {
        System.out.printf("turn=%d  phase=%s  absorbing=%b%n",
                turn, phase, absorbing);
    }

    private void step() {
        if (!darkState.verify()) {
            System.out.println("verify() failed — cannot advance.");
            return;
        }
        if (phase.isAbsorbing()) {
            System.out.println("already absorbing.");
            return;
        }
        turn++;
        phase = phase.next();
        if (phase.isAbsorbing()) {
            absorbing = true;
        }
        System.out.printf("advanced → %s%n", phase);
    }

    private void dark() {
        absorbing = true;
        phase = SovereigntyState.DARK_STATE;
        System.out.println("DARK_STATE engaged — absorbing terminal.");
    }

    private void printVerify() {
        boolean ok = darkState.verify();
        System.out.printf("verify=%b  residual=%.3e  seed=%.3e%n",
                ok, darkState.eigenvalueResidual(), darkState.quadraticSeedResidual());
    }

    private void help() {
        System.out.println("commands: status | step | dark | verify | help | exit");
    }

    public static void main(String[] args) {
        new GameplayConsole().run();
    }
}
