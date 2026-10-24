package com.fruitfly.games.rhythm.logic;

import java.util.ArrayList;
import java.util.List;

/**
 * Compact JSON summary of what the game's LIF-RK4 brain did recently, for
 * the CLI's {@code /llm} chat. Built only from state the simulators really
 * keep: per-lane spike times ({@link SpikeWindow}), each lane neuron's
 * membrane voltage ({@link LifNeuron#v()}), and, for the connectome
 * autoplayer, every circuit neuron's spike count and last spike
 * ({@link CircuitSim}). Nothing is invented: with no brain running the
 * snapshot says so ({@code "brain":"idle"}) and carries no lanes.
 *
 * <p>Shape (keys stable, numbers rounded to 0.1):
 * <pre>
 * {"v":1,"mode":"lif","brain":"lif","song_ms":5230,"brain_ms":5200,"window_ms":2000,
 *  "lanes":[{"lane":0,"label":"MB","spikes":3,"rate_hz":1.5,"last_ms":5101,"v_mv":-51.8,"total":12},…],
 *  "total_spikes":40,"top":[{"id":"lane0.out","region":"MB","spikes":12,"ms_since":99},…]}
 * </pre>
 */
public final class NeuronSnapshot {
    public static final long WINDOW_MS = 2000;
    public static final int MAX_TOP = 5;

    private NeuronSnapshot() {
    }

    /** No brain is driving presses (control mode off). */
    public static String idle(String mode, long songMs) {
        StringBuilder b = new StringBuilder(96);
        b.append("{\"v\":1,\"mode\":").append(Json.str(mode))
                .append(",\"brain\":\"idle\",\"song_ms\":").append(songMs)
                .append(",\"window_ms\":").append(WINDOW_MS)
                .append(",\"lanes\":[],\"total_spikes\":0,\"top\":[]}");
        return b.toString();
    }

    /** Four-lane LIF autoplayer: the lane neurons are the whole brain. */
    public static String fromLif(String mode, long songMs, LifAutoplayer a, String[] labels) {
        int lanes = RhythmGame.LANES;
        double[] v = new double[lanes];
        for (int l = 0; l < lanes; l++) {
            v[l] = a.neuron(l).v();
        }
        long now = a.brainTimeMs();
        SpikeWindow w = a.spikeWindow();
        List<Top> top = new ArrayList<>();
        for (int l = 0; l < lanes; l++) {
            long last = w.lastSpikeMs(l);
            if (last != Long.MIN_VALUE && last > now - WINDOW_MS) {
                top.add(new Top("lane" + l, label(labels, l), w.total(l), now - last));
            }
        }
        return build(mode, "lif", songMs, now, w, v, labels, a.spikeCount(), top);
    }

    /** Connectome autoplayer: lanes are laneN.out; top = most recently active circuit neurons. */
    public static String fromConnectome(String mode, long songMs, ConnectomeAutoplayer a, String[] labels) {
        int lanes = RhythmGame.LANES;
        CircuitSim sim = a.sim();
        double[] v = new double[lanes];
        for (int l = 0; l < lanes; l++) {
            v[l] = sim.neuron(a.outputIndex(l)).v();
        }
        long now = a.brainTimeMs();
        Circuit c = sim.circuit();
        List<Top> top = new ArrayList<>();
        for (int i = 0; i < c.neuronCount(); i++) {
            long s = sim.lastSpikeSubstep(i);
            if (s == Long.MIN_VALUE) {
                continue;
            }
            long last = (long) (s * LifNeuron.DT_MS);
            if (last > now - WINDOW_MS) {
                top.add(new Top(c.id(i), c.region(i), sim.spikeCount(i), now - last));
            }
        }
        return build(mode, "connectome", songMs, now, a.spikeWindow(), v, labels, a.spikeCount(), top);
    }

    /** Pure serializer; package-visible for tests. */
    static String build(String mode, String brain, long songMs, long brainMs, SpikeWindow w,
            double[] vMv, String[] labels, long totalSpikes, List<Top> top) {
        StringBuilder b = new StringBuilder(512);
        b.append("{\"v\":1,\"mode\":").append(Json.str(mode))
                .append(",\"brain\":").append(Json.str(brain))
                .append(",\"song_ms\":").append(songMs)
                .append(",\"brain_ms\":").append(brainMs)
                .append(",\"window_ms\":").append(WINDOW_MS)
                .append(",\"lanes\":[");
        for (int l = 0; l < w.lanes(); l++) {
            if (l > 0) {
                b.append(',');
            }
            int n = w.countInWindow(l, brainMs, WINDOW_MS);
            long last = w.lastSpikeMs(l);
            b.append("{\"lane\":").append(l)
                    .append(",\"label\":").append(Json.str(label(labels, l)))
                    .append(",\"spikes\":").append(n)
                    .append(",\"rate_hz\":").append(Json.num1(n * 1000.0 / WINDOW_MS))
                    .append(",\"last_ms\":").append(last == Long.MIN_VALUE ? "null" : String.valueOf(last))
                    .append(",\"v_mv\":").append(Json.num1(vMv[l]))
                    .append(",\"total\":").append(w.total(l))
                    .append('}');
        }
        b.append("],\"total_spikes\":").append(totalSpikes).append(",\"top\":[");
        // most recent first, then busiest; stable insertion sort (tiny lists)
        List<Top> sorted = new ArrayList<>(top);
        for (int i = 1; i < sorted.size(); i++) {
            Top x = sorted.get(i);
            int j = i - 1;
            while (j >= 0 && before(x, sorted.get(j))) {
                sorted.set(j + 1, sorted.get(j));
                j--;
            }
            sorted.set(j + 1, x);
        }
        for (int i = 0; i < sorted.size() && i < MAX_TOP; i++) {
            Top t = sorted.get(i);
            if (i > 0) {
                b.append(',');
            }
            b.append("{\"id\":").append(Json.str(t.id))
                    .append(",\"region\":").append(t.region == null ? "null" : Json.str(t.region))
                    .append(",\"spikes\":").append(t.spikes)
                    .append(",\"ms_since\":").append(t.msSince)
                    .append('}');
        }
        b.append("]}");
        return b.toString();
    }

    private static boolean before(Top a, Top b) {
        if (a.msSince != b.msSince) {
            return a.msSince < b.msSince;
        }
        return a.spikes > b.spikes;
    }

    private static String label(String[] labels, int l) {
        return labels != null && l < labels.length && labels[l] != null ? labels[l] : "lane" + l;
    }

    /** One active neuron in the snapshot's top list. */
    static final class Top {
        final String id;
        final String region;
        final long spikes;
        final long msSince;

        Top(String id, String region, long spikes, long msSince) {
            this.id = id;
            this.region = region;
            this.spikes = spikes;
            this.msSince = msSince;
        }
    }
}
