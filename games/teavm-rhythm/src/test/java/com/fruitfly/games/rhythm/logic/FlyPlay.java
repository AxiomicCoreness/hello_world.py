package com.fruitfly.games.rhythm.logic;

/** Plays a chart with each fly brain (no human input), as the browser loop does: brain first, then the game clock. */
final class FlyPlay {
    static final Circuit TOY = ConnectomeXml.parse(ToyCircuitXml.XML);
    static final int[] MODES = {ControlMode.LIF, ControlMode.CONNECTOME, ControlMode.ASSIST_LIF, ControlMode.ASSIST_CONNECTOME};

    private FlyPlay() {
    }

    /** [score, perfect, great, good, miss, notes]. */
    static long[] play(NoteChart chart, int mode, long frameMs) {
        RhythmGame g = new RhythmGame(chart.fresh());
        java.util.function.LongConsumer brain;
        switch (mode) {
            case ControlMode.LIF: brain = new LifAutoplayer(g)::advanceTo; break;
            case ControlMode.CONNECTOME: brain = new ConnectomeAutoplayer(g, TOY)::advanceTo; break;
            case ControlMode.ASSIST_LIF: {
                AssistArbiter a = new AssistArbiter(g);
                LifAutoplayer p = new LifAutoplayer(g, AssistArbiter.FLY_AIM_MS, a);
                a.attachBrain(p::advanceTo);
                brain = p::advanceTo;
                break;
            }
            case ControlMode.ASSIST_CONNECTOME: {
                AssistArbiter a = new AssistArbiter(g);
                ConnectomeAutoplayer p = new ConnectomeAutoplayer(g, TOY, AssistArbiter.FLY_AIM_MS, a);
                a.attachBrain(p::advanceTo);
                brain = p::advanceTo;
                break;
            }
            default: throw new IllegalArgumentException("mode " + mode);
        }
        long end = g.chart().lastNoteMs() + 1000;
        for (long t = 0; t <= end; t += frameMs) {
            brain.accept(t);
            g.update(t);
        }
        brain.accept(end);
        g.update(end);
        return new long[] {g.score(), g.perfectCount(), g.greatCount(), g.goodCount(), g.missCount(), g.chart().notes().size()};
    }
}
