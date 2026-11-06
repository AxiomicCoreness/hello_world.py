// SPDX-FileCopyrightText: 2026 Clarke Yoursa Tee Luminara Atlas (MrTeanotCoffee) <mrteanotcoffee@gmail.com>
// SPDX-License-Identifier: MIT

package com.fruitfly.brain;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * Identification record for male-cns:v1.0 cell type CB2514.
 *
 * <p>The classpath resource {@code connectome/neuron_index.json} lists the
 * five public body IDs. It is not a {@link Connectome}: no synaptic edges
 * are included, and {@link #refuseConnectome()} never fabricates one.
 * PVLP(R) is loaded from {@code connectome/roi_context_PVLP_R.json} as
 * chart context only.
 */
public final class Cb2514NeuronIndex {
    public static final String RESOURCE = "connectome/neuron_index.json";
    public static final String ROI_RESOURCE = "connectome/roi_context_PVLP_R.json";
    public static final String STDERR_NOTE =
            "CB2514 neuron_index is identification only; ConnectomeLoader was not called. "
                    + "PVLP(R) is chart ROI context, not verified per-body membership or edges.";

    static final List<Long> EXPECTED_BODY_IDS = List.of(60536L, 64328L, 124180L, 125402L, 167164L);

    private final List<Long> bodyIds;
    private final String datasetId;
    private final String cellType;
    private final int lateralityLeft;
    private final int lateralityRight;
    private final String roiDisplay;

    private Cb2514NeuronIndex(
            List<Long> bodyIds,
            String datasetId,
            String cellType,
            int lateralityLeft,
            int lateralityRight,
            String roiDisplay) {
        this.bodyIds = List.copyOf(bodyIds);
        this.datasetId = datasetId;
        this.cellType = cellType;
        this.lateralityLeft = lateralityLeft;
        this.lateralityRight = lateralityRight;
        this.roiDisplay = roiDisplay;
    }

    public static Cb2514NeuronIndex loadDefault() throws IOException {
        ClassLoader loader = Cb2514NeuronIndex.class.getClassLoader();
        try (InputStream index = loader.getResourceAsStream(RESOURCE)) {
            if (index == null) {
                throw new IllegalArgumentException("classpath resource not found: " + RESOURCE);
            }
            try (InputStream roi = loader.getResourceAsStream(ROI_RESOURCE)) {
                if (roi == null) {
                    throw new IllegalArgumentException("classpath resource not found: " + ROI_RESOURCE);
                }
                return load(index, roi, "classpath:" + RESOURCE);
            }
        }
    }

    static Cb2514NeuronIndex load(InputStream index, InputStream roi, String source) throws IOException {
        Map<String, Object> indexObject = object(MiniJson.parse(read(index)), source);
        Map<String, Object> roiObject = object(MiniJson.parse(read(roi)), source + " roi");
        return fromMaps(indexObject, roiObject, source);
    }

    private static Cb2514NeuronIndex fromMaps(
            Map<String, Object> index, Map<String, Object> roi, String source) {
        if (!"clarke_cb2514_neuron_index/v1".equals(index.get("schema"))) {
            throw new IllegalArgumentException(source + ": unexpected neuron_index schema");
        }
        if (!"male-cns:v1.0".equals(index.get("dataset_id"))) {
            throw new IllegalArgumentException(source + ": dataset_id is not male-cns:v1.0");
        }
        if (!"CB2514".equals(index.get("cell_type"))) {
            throw new IllegalArgumentException(source + ": cell_type is not CB2514");
        }
        if (!Boolean.FALSE.equals(index.get("edges_included"))) {
            throw new IllegalArgumentException(source + ": edges_included must be false");
        }
        List<Long> bodyIds = longList(index.get("bodyIds"), source);
        if (!EXPECTED_BODY_IDS.equals(bodyIds)) {
            throw new IllegalArgumentException(source + ": bodyIds are not the five CB2514 ids");
        }
        Object count = index.get("count");
        if (!(count instanceof Long) || ((Long) count).longValue() != bodyIds.size()) {
            throw new IllegalArgumentException(source + ": count does not match bodyIds");
        }
        Map<String, Object> laterality = object(index.get("laterality"), source + " laterality");
        int left = requiredInt(laterality.get("L"), source + " laterality.L");
        int right = requiredInt(laterality.get("R"), source + " laterality.R");
        if (left != 3 || right != 2) {
            throw new IllegalArgumentException(source + ": laterality is not L=3 R=2");
        }
        List<Object> neurons = array(index.get("neurons"), source + " neurons");
        if (neurons.size() != bodyIds.size()) {
            throw new IllegalArgumentException(source + ": neurons length mismatch");
        }
        for (int i = 0; i < neurons.size(); i++) {
            Map<String, Object> neuron = object(neurons.get(i), source + " neuron " + i);
            long bodyId = requiredLong(neuron.get("bodyId"), source + " neuron bodyId");
            if (bodyId != bodyIds.get(i)) {
                throw new IllegalArgumentException(source + ": neuron bodyId order mismatch");
            }
        }
        if (!"clarke_cb2514_roi_context/v1".equals(roi.get("schema"))) {
            throw new IllegalArgumentException(source + ": unexpected roi schema");
        }
        if (!"PVLP(R)".equals(roi.get("display"))) {
            throw new IllegalArgumentException(source + ": roi display is not PVLP(R)");
        }
        if (!Boolean.TRUE.equals(roi.get("chart_membership_unverified"))) {
            throw new IllegalArgumentException(source + ": chart membership must stay unverified");
        }
        if (!Boolean.FALSE.equals(roi.get("edges_inferred_from_charts"))) {
            throw new IllegalArgumentException(source + ": chart edges must stay false");
        }
        if (!"observed_chart_roi_context_only".equals(roi.get("role"))) {
            throw new IllegalArgumentException(source + ": roi role is not chart context");
        }
        if (!Boolean.TRUE.equals(roi.get("not_a_cell_type"))
                || !Boolean.TRUE.equals(roi.get("not_per_body_annotation"))) {
            throw new IllegalArgumentException(source + ": roi context flags are not identification-only");
        }
        return new Cb2514NeuronIndex(bodyIds, "male-cns:v1.0", "CB2514", left, right, "PVLP(R)");
    }

    public List<Long> bodyIds() {
        return bodyIds;
    }

    public String datasetId() {
        return datasetId;
    }

    public String cellType() {
        return cellType;
    }

    public int lateralityLeft() {
        return lateralityLeft;
    }

    public int lateralityRight() {
        return lateralityRight;
    }

    public String roiDisplay() {
        return roiDisplay;
    }

    public boolean edgesIncluded() {
        return false;
    }

    /** Always refuses. CB2514 metadata is not connectivity. */
    public Connectome refuseConnectome() {
        throw new IllegalStateException(
                "CB2514 neuron_index has no authentic edges; refusing to build a Connectome");
    }

    public String identificationLine() {
        StringBuilder ids = new StringBuilder();
        for (int i = 0; i < bodyIds.size(); i++) {
            if (i > 0) {
                ids.append(',');
            }
            ids.append(bodyIds.get(i));
        }
        return "cb2514 dataset=" + datasetId
                + " cell_type=" + cellType
                + " count=" + bodyIds.size()
                + " bodyIds=" + ids
                + " laterality_L=" + lateralityLeft
                + " laterality_R=" + lateralityRight
                + " edges=0"
                + " roi=" + roiDisplay
                + " chart_membership_unverified=true";
    }

    private static String read(InputStream in) throws IOException {
        return new String(in.readAllBytes(), StandardCharsets.UTF_8);
    }

    @SuppressWarnings("unchecked")
    private static Map<String, Object> object(Object value, String source) {
        if (!(value instanceof Map)) {
            throw new IllegalArgumentException(source + ": expected JSON object");
        }
        return (Map<String, Object>) value;
    }

    @SuppressWarnings("unchecked")
    private static List<Object> array(Object value, String source) {
        if (!(value instanceof List)) {
            throw new IllegalArgumentException(source + ": expected JSON array");
        }
        return (List<Object>) value;
    }

    private static List<Long> longList(Object value, String source) {
        List<Object> raw = array(value, source);
        List<Long> out = new ArrayList<>();
        for (Object item : raw) {
            out.add(requiredLong(item, source));
        }
        return out;
    }

    private static long requiredLong(Object value, String source) {
        if (!(value instanceof Long)) {
            throw new IllegalArgumentException(source + ": expected integer");
        }
        return ((Long) value).longValue();
    }

    private static int requiredInt(Object value, String source) {
        long number = requiredLong(value, source);
        if (number > Integer.MAX_VALUE) {
            throw new IllegalArgumentException(source + ": integer too large");
        }
        return (int) number;
    }
}
