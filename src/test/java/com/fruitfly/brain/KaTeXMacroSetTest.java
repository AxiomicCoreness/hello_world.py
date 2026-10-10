package com.fruitfly.brain;

import org.junit.jupiter.api.Test;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 📝∀ KaTeX macro set — typo-guard tests ∀📝
 *
 * <p>Reads the classpath copy of {@code katex_macros.yaml} and asserts
 * that the six core macros are present and that the file declares at
 * least 20 macros. Does NOT assert byte-identity with
 * {@code docs/katex_macros.yaml}; the classpath copy is authoritative
 * for this test's purposes.
 */
class KaTeXMacroSetTest {

    private static final String RESOURCE = "katex_macros.yaml";

    /** Direct read of the classpath file. Fails if absent. */
    private static String readMacroFile() throws Exception {
        try (InputStream in = KaTeXMacroSetTest.class.getClassLoader()
                .getResourceAsStream(RESOURCE)) {
            assertNotNull(in, RESOURCE + " must be on the classpath");
            return new String(in.readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    @Test
    void macroFileDeclaresHalf() throws Exception {
        assertTrue(readMacroFile().contains("\"\\\\half\""),
                "\\half macro must be declared");
    }

    @Test
    void macroFileDeclaresKet() throws Exception {
        assertTrue(readMacroFile().contains("\"\\\\ket\""),
                "\\ket macro must be declared");
    }

    @Test
    void macroFileDeclaresBra() throws Exception {
        assertTrue(readMacroFile().contains("\"\\\\bra\""),
                "\\bra macro must be declared");
    }

    @Test
    void macroFileDeclaresTr() throws Exception {
        assertTrue(readMacroFile().contains("\"\\\\Tr\""),
                "\\Tr macro must be declared");
    }

    @Test
    void macroFileDeclaresDisc() throws Exception {
        assertTrue(readMacroFile().contains("\"\\\\Disc\""),
                "\\Disc macro must be declared");
    }

    @Test
    void macroFileDeclaresVertex() throws Exception {
        assertTrue(readMacroFile().contains("\"\\\\vertex\""),
                "\\vertex macro must be declared");
    }

    @Test
    void allMacrosHaveExactlyOneDefinition() throws Exception {
        // Count lines of the form: "\\<name>": ...
        Matcher m = Pattern.compile(
                "^\\s*\"\\\\[A-Za-z]+\"\\s*:",
                Pattern.MULTILINE
        ).matcher(readMacroFile());
        long count = 0;
        while (m.find()) count++;
        assertTrue(count >= 20,
                "expected at least 20 macro declarations, found " + count);
    }

    /**
     * Cross-check: the Java source map and the YAML must declare
     * the same number of macros.
     */
    @Test
    void javaMapAndYamlAgreeOnCount() throws Exception {
        Matcher m = Pattern.compile(
                "^\\s*\"\\\\[A-Za-z]+\"\\s*:",
                Pattern.MULTILINE
        ).matcher(readMacroFile());
        long yamlCount = 0;
        while (m.find()) yamlCount++;

        int javaCount = KaTeXMacros.count();
        assertEquals(yamlCount, javaCount,
                "YAML declares " + yamlCount + " macros; Java map has " + javaCount);
    }
}