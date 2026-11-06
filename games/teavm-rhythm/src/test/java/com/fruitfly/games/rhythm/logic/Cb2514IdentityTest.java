// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT

package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.junit.jupiter.api.Test;

/** CB2514 identity aside matches the sovereign-brain neuron_index resource and is not a spike snapshot. */
class Cb2514IdentityTest {
    private static final Path INDEX = Paths.get("../../src/main/resources/connectome/neuron_index.json");

    @Test
    void asideMatchesCanonicalBodyIds() throws Exception {
        assertTrue(Files.isRegularFile(INDEX), INDEX.toAbsolutePath().toString());
        String json = Files.readString(INDEX);
        Matcher ids = Pattern.compile("\"bodyIds\"\\s*:\\s*\\[([^\\]]+)]").matcher(json);
        assertTrue(ids.find(), json);
        assertEquals("60536,64328,124180,125402,167164",
                ids.group(1).replace("\n", "").replace(" ", ""));
        assertTrue(json.contains("\"edges_included\": false"));
        assertTrue(json.contains("\"cell_type\": \"CB2514\""));
        String aside = NeuronSnapshot.cb2514IdentityAside();
        assertEquals(Cb2514Identity.asideJson(), aside);
        for (long id : Cb2514Identity.BODY_IDS) {
            assertTrue(aside.contains(Long.toString(id)), aside);
        }
        assertTrue(aside.contains("\"activity_present\":false"));
        assertTrue(aside.contains("\"chart_membership_unverified\":true"));
        assertTrue(aside.contains("\"not_rhythm_lanes\":true"));
        assertFalse(aside.contains("rate_hz"));
        assertFalse(aside.contains("synapses"));
        assertFalse(NeuronSnapshot.idle("off", 0).contains("CB2514"));
    }
}
