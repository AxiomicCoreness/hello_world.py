// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT

package com.fruitfly.games.rhythm.logic;

/**
 * Identification aside for the five public male-cns:v1.0 CB2514 body IDs.
 * This is not a spike snapshot and not a synaptic circuit. The rhythm lanes
 * stay on {@link NeuronSnapshot}'s existing builders.
 */
public final class Cb2514Identity {
    public static final long[] BODY_IDS = {60536L, 64328L, 124180L, 125402L, 167164L};

    private Cb2514Identity() {
    }

    public static String asideJson() {
        StringBuilder b = new StringBuilder(320);
        b.append("{\"v\":1,\"kind\":\"cb2514_identity_aside\",\"dataset_id\":\"male-cns:v1.0\",");
        b.append("\"cell_type\":\"CB2514\",\"bodyIds\":[");
        for (int i = 0; i < BODY_IDS.length; i++) {
            if (i > 0) {
                b.append(',');
            }
            b.append(BODY_IDS[i]);
        }
        b.append("],\"activity_present\":false,\"edges_included\":false,");
        b.append("\"not_rhythm_lanes\":true,\"roi_context\":{\"display\":\"PVLP(R)\",");
        b.append("\"role\":\"observed_chart_roi_context_only\",\"chart_membership_unverified\":true},");
        b.append("\"resource\":\"src/main/resources/connectome/neuron_index.json\"}");
        return b.toString();
    }
}
