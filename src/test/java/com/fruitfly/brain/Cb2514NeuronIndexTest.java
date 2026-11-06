// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT

package com.fruitfly.brain;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.ByteArrayInputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;

import org.junit.jupiter.api.Test;

class Cb2514NeuronIndexTest {

    @Test
    void classpathIndexIsTheFivePublicBodies() throws Exception {
        Cb2514NeuronIndex index = Cb2514NeuronIndex.loadDefault();
        assertEquals(List.of(60536L, 64328L, 124180L, 125402L, 167164L), index.bodyIds());
        assertEquals("male-cns:v1.0", index.datasetId());
        assertEquals("CB2514", index.cellType());
        assertEquals(3, index.lateralityLeft());
        assertEquals(2, index.lateralityRight());
        assertEquals("PVLP(R)", index.roiDisplay());
        assertFalse(index.edgesIncluded());
        assertEquals(
                "cb2514 dataset=male-cns:v1.0 cell_type=CB2514 count=5 "
                        + "bodyIds=60536,64328,124180,125402,167164 laterality_L=3 laterality_R=2 "
                        + "edges=0 roi=PVLP(R) chart_membership_unverified=true",
                index.identificationLine());
    }

    @Test
    void refusesToBuildAConnectome() throws Exception {
        Cb2514NeuronIndex index = Cb2514NeuronIndex.loadDefault();
        IllegalStateException ex = assertThrows(IllegalStateException.class, index::refuseConnectome);
        assertTrue(ex.getMessage().contains("no authentic edges"));
    }

    @Test
    void rejectsAnIndexThatClaimsEdges() {
        String index = "{\"schema\":\"clarke_cb2514_neuron_index/v1\",\"dataset_id\":\"male-cns:v1.0\","
                + "\"cell_type\":\"CB2514\",\"edges_included\":true,\"count\":5,"
                + "\"bodyIds\":[60536,64328,124180,125402,167164],\"laterality\":{\"L\":3,\"R\":2},"
                + "\"neurons\":[{\"bodyId\":60536},{\"bodyId\":64328},{\"bodyId\":124180},"
                + "{\"bodyId\":125402},{\"bodyId\":167164}]}";
        String roi = "{\"schema\":\"clarke_cb2514_roi_context/v1\",\"display\":\"PVLP(R)\","
                + "\"chart_membership_unverified\":true,\"edges_inferred_from_charts\":false,"
                + "\"role\":\"observed_chart_roi_context_only\",\"not_a_cell_type\":true,"
                + "\"not_per_body_annotation\":true}";
        IllegalArgumentException ex = assertThrows(IllegalArgumentException.class, () -> Cb2514NeuronIndex.load(
                new ByteArrayInputStream(index.getBytes(StandardCharsets.UTF_8)),
                new ByteArrayInputStream(roi.getBytes(StandardCharsets.UTF_8)),
                "test"));
        assertTrue(ex.getMessage().contains("edges_included"));
    }

    @Test
    void edgeSchemaResourceStatesEdgesAreAbsent() throws Exception {
        try (var in = Cb2514NeuronIndexTest.class.getClassLoader()
                .getResourceAsStream("connectome/connectivity_edge_schema.json")) {
            assertTrue(in != null);
            String text = new String(in.readAllBytes(), StandardCharsets.UTF_8);
            assertTrue(text.contains("\"edges_in_tree\": false"));
            assertFalse(text.contains("\"pre_bodyId\": 60536"));
        }
    }
}
