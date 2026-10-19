package com.fruitfly.brain;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.ErrorHandler;
import org.xml.sax.SAXException;
import org.xml.sax.SAXParseException;

/**
 * Builds a {@link Connectome} from a small XML connectivity file.
 *
 * <p>Expected format (this is a project-local format, <b>not</b> the
 * FlyEM/neuPrint hemibrain export, which ships as CSV tables):
 * <pre>
 * &lt;hemibrain&gt;
 *   &lt;neuron id="A"/&gt;
 *   &lt;neuron id="B"/&gt;
 *   &lt;connection from="A" to="B" weight="1.0" delayMs="2.5"/&gt;
 * &lt;/hemibrain&gt;
 * </pre>
 *
 * <ul>
 *   <li>Neuron ids are non-empty strings, mapped to indices 0..n-1 in
 *       document order. Duplicate ids are rejected.</li>
 *   <li>{@code from}/{@code to} must name declared neurons.</li>
 *   <li>{@code weight} is required and must be finite (negative =
 *       inhibitory, as in {@link Connectome#random}).</li>
 *   <li>{@code delayMs} is optional, default {@value #DEFAULT_DELAY_MS} ms
 *       (the lower bound of {@code random()}'s 1..4 ms range), must be
 *       finite and &gt; 0.</li>
 *   <li>Self-loops ({@code from == to}) are allowed, although
 *       {@code random()} never generates them. A repeated (from, to)
 *       pair is rejected.</li>
 *   <li>CSR rows are ordered by source index; within a row, synapses
 *       keep document order.</li>
 * </ul>
 *
 * <p>The parser is hardened against XXE: DOCTYPE declarations are
 * refused outright and external entities / DTDs / XInclude are off.
 * JDK only, no third-party dependencies.
 */
public final class ConnectomeLoader {

    /** Default synaptic delay when a connection has no delayMs attribute. */
    public static final double DEFAULT_DELAY_MS = 1.0;

    private static final String ROOT = "hemibrain";

    /**
     * Load a connectome from an XML file on disk.
     *
     * @throws IllegalArgumentException if the file is missing or the
     *         content is malformed or invalid
     * @throws IOException on a read failure
     */
    public static Connectome loadFromXml(final Path file) throws IOException {
        if (file == null) {
            throw new IllegalArgumentException("connectome path must be non-null");
        }
        if (!Files.isRegularFile(file)) {
            throw new IllegalArgumentException("connectome file not found: " + file);
        }
        try (InputStream in = Files.newInputStream(file)) {
            return load(in, file.toString());
        }
    }

    /**
     * Load a connectome from a classpath resource, e.g. "HHMIJaneliaMap.xml".
     *
     * @throws IllegalArgumentException if the resource is absent or invalid
     * @throws IOException on a read failure
     */
    public static Connectome loadFromResource(final String name) throws IOException {
        if (name == null || name.isEmpty()) {
            throw new IllegalArgumentException("resource name must be non-empty");
        }
        final ClassLoader cl = ConnectomeLoader.class.getClassLoader();
        try (InputStream in = cl.getResourceAsStream(name)) {
            if (in == null) {
                throw new IllegalArgumentException("classpath resource not found: " + name);
            }
            return load(in, "classpath:" + name);
        }
    }

    /** Load from an open stream; {@code source} is used in error messages only. */
    public static Connectome load(final InputStream in, final String source) throws IOException {
        final Document doc = parse(in, source);
        final Element root = doc.getDocumentElement();
        if (!ROOT.equals(root.getTagName())) {
            throw new IllegalArgumentException(source + ": root element must be <" + ROOT
                    + ">, found <" + root.getTagName() + ">");
        }

        // 1. Neurons -> indices in document order.
        final Map<String, Integer> index = new LinkedHashMap<>();
        final NodeList neurons = root.getElementsByTagName("neuron");
        for (int i = 0; i < neurons.getLength(); i++) {
            final Element el = (Element) neurons.item(i);
            final String id = required(el, "id", source, "neuron #" + i);
            if (index.putIfAbsent(id, index.size()) != null) {
                throw new IllegalArgumentException(source + ": duplicate neuron id '" + id + "'");
            }
        }
        final int n = index.size();

        // 2. Connections, bucketed per source row (keeps document order).
        final List<List<double[]>> rows = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            rows.add(new ArrayList<>());
        }
        final Set<Long> seen = new HashSet<>();
        final NodeList conns = root.getElementsByTagName("connection");
        for (int k = 0; k < conns.getLength(); k++) {
            final Element el = (Element) conns.item(k);
            final String where = "connection #" + k;
            final String from = required(el, "from", source, where);
            final String to = required(el, "to", source, where);
            final Integer pre = index.get(from);
            if (pre == null) {
                throw new IllegalArgumentException(source + ": " + where
                        + " references unknown source neuron '" + from + "'");
            }
            final Integer post = index.get(to);
            if (post == null) {
                throw new IllegalArgumentException(source + ": " + where
                        + " references unknown target neuron '" + to + "'");
            }
            final double w = number(required(el, "weight", source, where), "weight", source, where);
            final double d = el.hasAttribute("delayMs")
                    ? number(el.getAttribute("delayMs"), "delayMs", source, where)
                    : DEFAULT_DELAY_MS;
            if (d <= 0.0) {
                throw new IllegalArgumentException(source + ": " + where
                        + " delayMs must be > 0, got " + d);
            }
            if (!seen.add(((long) pre << 32) | post)) {
                throw new IllegalArgumentException(source + ": duplicate connection "
                        + from + " -> " + to);
            }
            rows.get(pre).add(new double[] {post, w, d});
        }

        // 3. CSR.
        final int nnz = seen.size();
        final int[] rowPtr = new int[n + 1];
        final int[] colIdx = new int[nnz];
        final double[] weight = new double[nnz];
        final double[] delayMs = new double[nnz];
        int k = 0;
        for (int i = 0; i < n; i++) {
            rowPtr[i] = k;
            for (double[] syn : rows.get(i)) {
                colIdx[k] = (int) syn[0];
                weight[k] = syn[1];
                delayMs[k] = syn[2];
                k++;
            }
        }
        rowPtr[n] = k;
        return new Connectome(n, rowPtr, colIdx, weight, delayMs);
    }

    private static Document parse(final InputStream in, final String source) throws IOException {
        try {
            final DocumentBuilderFactory f = DocumentBuilderFactory.newInstance();
            f.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
            f.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            f.setFeature("http://xml.org/sax/features/external-general-entities", false);
            f.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
            f.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false);
            f.setAttribute(XMLConstants.ACCESS_EXTERNAL_DTD, "");
            f.setAttribute(XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
            f.setXIncludeAware(false);
            f.setExpandEntityReferences(false);
            f.setNamespaceAware(false);
            final DocumentBuilder b = f.newDocumentBuilder();
            b.setErrorHandler(new ErrorHandler() { // keep the JDK from printing "[Fatal Error]" to stderr
                @Override public void warning(SAXParseException e) { }
                @Override public void error(SAXParseException e) throws SAXException { throw e; }
                @Override public void fatalError(SAXParseException e) throws SAXException { throw e; }
            });
            final Document doc = b.parse(in);
            doc.getDocumentElement().normalize();
            return doc;
        } catch (ParserConfigurationException e) {
            throw new IllegalStateException("XML parser lacks required hardening features", e);
        } catch (SAXException e) {
            throw new IllegalArgumentException(source + ": invalid XML: " + e.getMessage(), e);
        }
    }

    private static String required(final Element el, final String attr,
                                   final String source, final String where) {
        if (!el.hasAttribute(attr) || el.getAttribute(attr).trim().isEmpty()) {
            throw new IllegalArgumentException(source + ": " + where
                    + " is missing required attribute '" + attr + "'");
        }
        return el.getAttribute(attr).trim();
    }

    private static double number(final String raw, final String attr,
                                 final String source, final String where) {
        final double v;
        try {
            v = Double.parseDouble(raw);
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException(source + ": " + where + " " + attr
                    + " is not a number: '" + raw + "'");
        }
        if (!Double.isFinite(v)) {
            throw new IllegalArgumentException(source + ": " + where + " " + attr
                    + " must be finite, got " + raw);
        }
        return v;
    }

    private ConnectomeLoader() {}
}
