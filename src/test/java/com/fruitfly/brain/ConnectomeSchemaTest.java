package com.fruitfly.brain;

import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

import javax.xml.XMLConstants;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.SAXParserFactory;
import javax.xml.transform.sax.SAXSource;
import javax.xml.transform.stream.StreamSource;
import javax.xml.validation.Schema;
import javax.xml.validation.SchemaFactory;
import javax.xml.validation.Validator;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NodeList;
import org.xml.sax.ErrorHandler;
import org.xml.sax.InputSource;
import org.xml.sax.SAXException;
import org.xml.sax.SAXParseException;
import org.xml.sax.XMLReader;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Checks src/main/resources/connectome.xsd against ConnectomeLoader.
 *
 * <p>Validation uses javax.xml.validation with secure processing on and
 * external DTD/schema access disabled. Input is fed through a SAX parser
 * hardened like the loader's (DOCTYPE refused), so XXE input is rejected
 * before validation.
 *
 * <p>Where the schema and the loader intentionally disagree, the case is
 * listed in {@link #documentedDisagreementsLoaderAcceptsSchemaRejects()}
 * and asserted in that direction, so a future change to either side
 * makes that test fail instead of drifting silently.
 */
class ConnectomeSchemaTest {

    private static final String XSD = "connectome.xsd";
    private static final String MAP = "HHMIJaneliaMap.xml";
    private static Schema schema;

    @BeforeAll
    static void loadSchema() throws Exception {
        SchemaFactory sf = SchemaFactory.newInstance(XMLConstants.W3C_XML_SCHEMA_NS_URI);
        sf.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
        sf.setProperty(XMLConstants.ACCESS_EXTERNAL_DTD, "");
        sf.setProperty(XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
        URL url = ConnectomeSchemaTest.class.getClassLoader().getResource(XSD);
        assertNotNull(url, XSD + " must be on the classpath (src/main/resources)");
        try (InputStream in = url.openStream()) {
            schema = sf.newSchema(new StreamSource(in, url.toString()));
        }
    }

    /** Validate; returns null if valid, else the error message. */
    private static String schemaError(InputStream in) {
        try {
            SAXParserFactory pf = SAXParserFactory.newInstance();
            pf.setNamespaceAware(true);
            pf.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
            pf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
            pf.setFeature("http://xml.org/sax/features/external-general-entities", false);
            pf.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
            pf.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false);
            pf.setXIncludeAware(false);
            XMLReader reader = pf.newSAXParser().getXMLReader();

            Validator v = schema.newValidator();
            v.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
            v.setProperty(XMLConstants.ACCESS_EXTERNAL_DTD, "");
            v.setProperty(XMLConstants.ACCESS_EXTERNAL_SCHEMA, "");
            ErrorHandler strict = new ErrorHandler() {
                @Override public void warning(SAXParseException e) { }
                @Override public void error(SAXParseException e) throws SAXException { throw e; }
                @Override public void fatalError(SAXParseException e) throws SAXException { throw e; }
            };
            reader.setErrorHandler(strict);
            v.setErrorHandler(strict);
            v.validate(new SAXSource(reader, new InputSource(in)));
            return null;
        } catch (SAXException e) {
            return String.valueOf(e.getMessage());
        } catch (Exception e) {
            throw new AssertionError("validator setup/IO failure", e);
        }
    }

    private static String schemaError(String xml) {
        return schemaError(new ByteArrayInputStream(xml.getBytes(StandardCharsets.UTF_8)));
    }

    private static boolean schemaValid(String xml) {
        return schemaError(xml) == null;
    }

    private static boolean loaderAccepts(String xml) {
        try {
            ConnectomeLoader.load(new ByteArrayInputStream(xml.getBytes(StandardCharsets.UTF_8)), "t");
            return true;
        } catch (IllegalArgumentException e) {
            return false;
        } catch (IOException e) {
            throw new AssertionError(e);
        }
    }

    private static void assertBothAccept(String xml) {
        assertTrue(loaderAccepts(xml), "loader should accept: " + xml);
        String err = schemaError(xml);
        assertNull(err, "schema should accept: " + xml + " -> " + err);
    }

    private static void assertBothReject(String xml) {
        assertFalse(loaderAccepts(xml), "loader should reject: " + xml);
        assertFalse(schemaValid(xml), "schema should reject: " + xml);
    }

    private static final String AB = "<hemibrain><neuron id='A'/><neuron id='B'/>";

    @Test
    void schemaIsPackagedFromMainResources() {
        URL url = getClass().getClassLoader().getResource(XSD);
        assertNotNull(url);
        // Maven copies src/main/resources to target/classes (pom only overrides testResources).
        assertFalse(url.toString().contains("test-classes"), url.toString());
    }

    @Test
    void janeliaMapPlaceholderValidates() throws IOException {
        try (InputStream in = getClass().getClassLoader().getResourceAsStream(MAP)) {
            assertNotNull(in);
            assertNull(schemaError(in));
        }
        assertEquals(3, ConnectomeLoader.loadFromResource(MAP).neuronCount());
    }

    @Test
    void validLoaderTestFixturesValidate() {
        // From ConnectomeLoaderTest.rowsAreSortedBySourceAndDelayIsParsed
        assertBothAccept("<hemibrain><neuron id='x'/><neuron id='y'/><neuron id='z'/>"
                + "<connection from='z' to='x' weight='-0.25' delayMs='3.5'/>"
                + "<connection from='x' to='z' weight='0.1'/>"
                + "<connection from='x' to='y' weight='0.2'/>"
                + "<connection from='y' to='y' weight='0.3'/></hemibrain>");
    }

    @Test
    void invalidLoaderTestFixturesRejected() {
        // Every rejecting fixture in ConnectomeLoaderTest.
        assertBothReject("<hemibrain><neuron id='A'/><neuron id='A'/></hemibrain>");
        assertBothReject("<hemibrain><neuron id='A'/><connection from='A' to='Q' weight='1'/></hemibrain>");
        assertBothReject(AB + "<connection from='A' to='B' weight='NaN'/></hemibrain>");
        assertBothReject(AB + "<connection from='A' to='B' weight='Infinity'/></hemibrain>");
        assertBothReject(AB + "<connection from='A' to='B'/></hemibrain>");
        assertBothReject(AB + "<connection from='A' to='B' weight='1' delayMs='0'/></hemibrain>");
        assertBothReject(AB + "<connection from='A' to='B' weight='1'/>"
                + "<connection from='A' to='B' weight='2'/></hemibrain>");
        assertBothReject("<brain/>");
        String xxe = "<?xml version='1.0'?>\n<!DOCTYPE hemibrain [<!ENTITY xxe SYSTEM 'file:///etc/hostname'>]>\n"
                + "<hemibrain><neuron id='&xxe;'/></hemibrain>";
        assertBothReject(xxe);
        assertTrue(schemaError(xxe).contains("DOCTYPE"), schemaError(xxe));
    }

    @Test
    void furtherSchemaInvalidCasesAgree() {
        assertBothReject("<hemibrain><neuron id='A'/><connection from='Q' to='A' weight='1'/></hemibrain>");
        assertBothReject("<hemibrain><neuron/></hemibrain>");
        assertBothReject("<hemibrain><neuron id=''/></hemibrain>");
        assertBothReject("<hemibrain><neuron id='   '/></hemibrain>");
        assertBothReject(AB + "<connection to='B' weight='1'/></hemibrain>");
        assertBothReject(AB + "<connection from='A' weight='1'/></hemibrain>");
        assertBothReject(AB + "<connection from='A' to='B' weight=''/></hemibrain>");
        assertBothReject(AB + "<connection from='A' to='B' weight='abc'/></hemibrain>");
        assertBothReject(AB + "<connection from='A' to='B' weight='INF'/></hemibrain>");
        assertBothReject(AB + "<connection from='A' to='B' weight='-INF'/></hemibrain>");
        assertBothReject(AB + "<connection from='A' to='B' weight='1e400'/></hemibrain>");
        assertBothReject(AB + "<connection from='A' to='B' weight='1' delayMs=''/></hemibrain>");
        assertBothReject(AB + "<connection from='A' to='B' weight='1' delayMs='-1'/></hemibrain>");
        assertBothReject(AB + "<connection from='A' to='B' weight='1' delayMs='-0'/></hemibrain>");
        assertBothReject(AB + "<connection from='A' to='B' weight='1' delayMs='NaN'/></hemibrain>");
        assertBothReject(AB + "<connection from='A' to='B' weight='1' delayMs='1e999'/></hemibrain>");
    }

    @Test
    void malformedXmlRejected() {
        assertBothReject("");
        assertBothReject("<hemibrain>");
        assertBothReject("<hemibrain><neuron id='A'></hemibrain>");
        assertBothReject("<hemibrain><neuron id=A/></hemibrain>");
        assertBothReject("not xml at all");
        assertBothReject("<hemibrain/><hemibrain/>");
    }

    @Test
    void edgeCasesBothAccept() {
        assertBothAccept("<hemibrain/>");
        assertBothAccept("<hemibrain></hemibrain>");
        assertBothAccept("<hemibrain><!-- c --><neuron id='A'/><?pi x?></hemibrain>");
        assertBothAccept("<hemibrain><connection from='B' to='A' weight='1'/>"
                + "<neuron id='A'/><neuron id='B'/></hemibrain>");          // any order
        assertBothAccept("<hemibrain><neuron id='A'/><connection from='A' to='A' weight='1'/></hemibrain>");
        assertBothAccept(AB + "<connection from='A' to='B' weight='1'/>"
                + "<connection from='B' to='A' weight='1'/></hemibrain>"); // reverse pair is distinct
        assertBothAccept(AB + "<connection from='A' to='B' weight='-0'/></hemibrain>");
        assertBothAccept(AB + "<connection from='A' to='B' weight='+.5' delayMs='5.'/></hemibrain>");
        assertBothAccept(AB + "<connection from='A' to='B' weight='1E3' delayMs=' 2.5 '/></hemibrain>");
        assertBothAccept(AB + "<connection from='A' to='B' weight='1' delayMs='1e-300'/></hemibrain>");
        assertBothAccept("<hemibrain><neuron id='a b'/><neuron id='&#931;'/>"
                + "<connection from='a b' to='&#931;' weight='2'/></hemibrain>");
        assertBothAccept("<hemibrain xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance'"
                + " xsi:noNamespaceSchemaLocation='connectome.xsd'/>");
    }

    /**
     * Cases where the schema is stricter than the loader. The loader
     * uses a namespace-unaware DOM (line 195), getElementsByTagName
     * descendant search (lines 116, 132), ignores unknown elements,
     * attributes and text, trims ids (line 218) and uses
     * Double.parseDouble (line 225). The schema rejects all of these.
     * There is no known case in the other direction (schema-valid but
     * loader-rejected).
     */
    @Test
    void documentedDisagreementsLoaderAcceptsSchemaRejects() {
        Map<String, String> cases = new LinkedHashMap<>();
        cases.put("unknown child element", "<hemibrain><meta/><neuron id='A'/></hemibrain>");
        cases.put("unknown attribute", "<hemibrain><neuron id='A' type='KC'/></hemibrain>");
        cases.put("text content", "<hemibrain>hello<neuron id='A'/></hemibrain>");
        cases.put("neuron nested in wrapper", "<hemibrain><group><neuron id='A'/></group></hemibrain>");
        cases.put("neuron nested in neuron", "<hemibrain><neuron id='A'><neuron id='B'/></neuron></hemibrain>");
        cases.put("default namespace", "<hemibrain xmlns='urn:x'><neuron id='A'/></hemibrain>");
        cases.put("prefixed child ignored by loader",
                "<hemibrain xmlns:p='urn:x'><p:neuron id='A'/></hemibrain>");
        cases.put("id with surrounding spaces", "<hemibrain><neuron id=' A '/></hemibrain>");
        cases.put("ref with surrounding spaces",
                AB + "<connection from=' A' to='B ' weight='1'/></hemibrain>");
        cases.put("Java double suffix d", AB + "<connection from='A' to='B' weight='1d'/></hemibrain>");
        cases.put("Java float suffix f", AB + "<connection from='A' to='B' weight='1.5f'/></hemibrain>");
        cases.put("Java hex double", AB + "<connection from='A' to='B' weight='0x1p3'/></hemibrain>");
        List<String> problems = new ArrayList<>();
        cases.forEach((name, xml) -> {
            if (!loaderAccepts(xml)) problems.add(name + ": loader now rejects");
            if (schemaValid(xml)) problems.add(name + ": schema now accepts");
        });
        assertTrue(problems.isEmpty(), "disagreement list out of date: " + problems);
    }

    @Test
    void xsdDelayDefaultMatchesLoaderConstant() throws Exception {
        DocumentBuilderFactory f = DocumentBuilderFactory.newInstance();
        f.setNamespaceAware(true);
        f.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
        f.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        Document d;
        try (InputStream in = getClass().getClassLoader().getResourceAsStream(XSD)) {
            d = f.newDocumentBuilder().parse(in);
        }
        NodeList attrs = d.getElementsByTagNameNS(XMLConstants.W3C_XML_SCHEMA_NS_URI, "attribute");
        Map<String, Element> byName = new LinkedHashMap<>();
        for (int i = 0; i < attrs.getLength(); i++) {
            Element a = (Element) attrs.item(i);
            byName.put(a.getAttribute("name"), a);
        }
        assertEquals(ConnectomeLoader.DEFAULT_DELAY_MS,
                Double.parseDouble(byName.get("delayMs").getAttribute("default")), 0.0);
        assertEquals("optional", byName.get("delayMs").getAttribute("use"));
        for (String req : new String[] {"id", "from", "to", "weight"}) {
            assertEquals("required", byName.get(req).getAttribute("use"), req);
            assertFalse(byName.get(req).hasAttribute("default"), req);
        }
    }

    /** Seeded random documents with mutations both sides should judge identically. */
    @Test
    void generatedCasesAgree() {
        Random rng = new Random(20261019L);
        String[] badWeights = {"NaN", "INF", "-INF", "Infinity", "", "x", "1e400", "--1"};
        String[] goodWeights = {"0", "-0.5", "1", "2.5e-3", "-7E2", "+3", ".25"};
        String[] badDelays = {"0", "-1", "", "NaN", "INF", "1e999", "-0.0", "1e-400"};
        String[] goodDelays = {"0.5", "1", "3.25", "1e2", "4."};
        int accepted = 0, rejected = 0;
        for (int t = 0; t < 600; t++) {
            int n = rng.nextInt(5);
            List<String> ids = new ArrayList<>();
            for (int i = 0; i < n; i++) ids.add("n" + i);
            StringBuilder body = new StringBuilder();
            List<String> parts = new ArrayList<>();
            for (String id : ids) parts.add("<neuron id='" + id + "'/>");
            java.util.Set<String> pairs = new java.util.HashSet<>();
            int m = n == 0 ? 0 : rng.nextInt(n * n + 1);
            for (int k = 0; k < m; k++) {
                String a = ids.get(rng.nextInt(n)), b = ids.get(rng.nextInt(n));
                if (!pairs.add(a + ">" + b)) continue;
                String delay = rng.nextBoolean() ? ""
                        : " delayMs='" + goodDelays[rng.nextInt(goodDelays.length)] + "'";
                parts.add("<connection from='" + a + "' to='" + b + "' weight='"
                        + goodWeights[rng.nextInt(goodWeights.length)] + "'" + delay + "/>");
            }
            switch (rng.nextInt(10)) {
                case 0: if (n > 0) parts.add("<neuron id='" + ids.get(rng.nextInt(n)) + "'/>"); break;
                case 1: if (n > 0) parts.add("<connection from='" + ids.get(0) + "' to='ghost' weight='1'/>"); break;
                case 2: if (n > 0) parts.add("<connection from='ghost' to='" + ids.get(0) + "' weight='1'/>"); break;
                case 3: if (n > 0 && !pairs.isEmpty()) {
                            String p = pairs.iterator().next();
                            String[] ab = p.split(">");
                            parts.add("<connection from='" + ab[0] + "' to='" + ab[1] + "' weight='9'/>");
                        } break;
                case 4: if (n > 0) parts.add("<connection from='" + ids.get(0) + "' to='" + ids.get(0)
                        + "x' weight='" + badWeights[rng.nextInt(badWeights.length)] + "'/>"); break;
                case 5: if (n > 1) { parts.add("<neuron id='z'/>"); parts.add("<connection from='z' to='z' weight='"
                        + badWeights[rng.nextInt(badWeights.length)] + "'/>"); } break;
                case 6: parts.add("<neuron id='q'/><connection from='q' to='q' weight='1' delayMs='"
                        + badDelays[rng.nextInt(badDelays.length)] + "'/>"); break;
                case 7: parts.add("<neuron id=''/>"); break;
                case 8: parts.add("<neuron id='q'/><connection from='q' to='q'/>"); break;
                default: break; // unmutated
            }
            java.util.Collections.shuffle(parts, rng);
            for (String p : parts) body.append(p);
            String xml = "<hemibrain>" + body + "</hemibrain>";
            boolean l = loaderAccepts(xml), s = schemaValid(xml);
            assertEquals(l, s, "loader=" + l + " schema=" + s + " for " + xml + " :: " + schemaError(xml));
            if (l) accepted++; else rejected++;
        }
        assertTrue(accepted > 100 && rejected > 100, "accepted=" + accepted + " rejected=" + rejected);
    }
}
