package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import javax.xml.XMLConstants;
import javax.xml.transform.stream.StreamSource;
import javax.xml.validation.SchemaFactory;
import javax.xml.validation.Validator;
import org.junit.jupiter.api.Test;

/** The embedded toy circuit matches the served XML file, and that file is valid against the repo's connectome.xsd. */
class ToyCircuitXmlTest {
    private static final Path FILE = Paths.get("src/main/webapp", ToyCircuitXml.PATH);
    private static final Path XSD = Paths.get("../../src/main/resources/connectome.xsd");

    @Test
    void embeddedCopyMatchesFile() throws Exception {
        assertEquals(Files.readString(FILE), ToyCircuitXml.XML, "run python3 tools/gen_toy_circuit_java.py");
    }

    @Test
    void fileIsLabelledToy() throws Exception {
        String s = Files.readString(FILE);
        assertTrue(s.contains("TOY CIRCUIT. This is NOT the Drosophila connectome"));
    }

    @Test
    void validAgainstRepoXsd() throws Exception {
        assertTrue(Files.isRegularFile(XSD), XSD.toAbsolutePath().toString());
        SchemaFactory sf = SchemaFactory.newInstance(XMLConstants.W3C_XML_SCHEMA_NS_URI);
        sf.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
        Validator v = sf.newSchema(XSD.toFile()).newValidator();
        v.validate(new StreamSource(new StringReader(ToyCircuitXml.XML)));
    }
}
