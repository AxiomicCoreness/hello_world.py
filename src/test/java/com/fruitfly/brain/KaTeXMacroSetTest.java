package com.fruitfly.brain;

import org.junit.jupiter.api.Test;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 🜁∀ KaTeX macro set — typo-guard tests ∀🜁
 *
 * <p>Reads the classpath copy of {@code katex_macros.yaml} and asserts
 * that the six core macros are present and that the file declares at
 * least 20 macros. Does NOT assert byte-identity with
 * {@code docs/katex_macros.yaml}; the classpath copy is authoritative
 * for this test's purposes.
 *
 * <p>Pattern robustness notes:
 * <ul>
 *   <li>The pattern matches one or two backslashes before the macro
 *       name, so it works whether the YAML generator emits a single
 *       or a double backslash in the raw file.</li>
 *   <li>Comment lines and the {@code katex:} / {@code macros:}
 *       wrapper keys are stripped before counting.</li>
 * </ul>
 */
class KaTeXMacroSetTest {

    private static final String RESOURCE = "katex_macros.yaml";

    /** Matches `"\\name":` or `"\name":` with optional leading whitespace. */
    private static final Pattern MACRO_LINE = Pattern.compile(
            "^\\s*\"\\\\{1,2}[A-Za-z]+\"\\s*:",
            Pattern.MULTILINE
    );

    /** Direct read of the classpath file. Fails if absent. */
    private static String readMacroFile() throws Exception {
        try (InputStream in = KaTeXMacroSetTest.class.getClassLoader()
                .getResourceAsStream(RESOURCE)) {
            assertNotNull(in, RESOURCE + " must be on the classpath");
            return new String(in.readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    /**
     * Remove comment lines and the two wrapper keys so the macro-count
     * pattern only sees macro declarations.
     */
    private static String stripCommentsAndWrappers(String yaml) {
        StringBuilder out = new StringBuilder();
        for (String line : yaml.split("\n", -1)) {
            String t = line.stripLeading();
            if (t.startsWith("#")) continue;
            if (t.startsWith("katex:")) continue;
            if (t.startsWith("macros:")) continue;
            out.append(line).append('\n');
        }
        return out.toString();
    }

    /** Count macro declarations in the given YAML text. */
    private static long countMacros(String yaml) {
        String cleaned = stripCommentsAndWrappers(yaml);
        Matcher m = MACRO_LINE.matcher(cleaned);
        long n = 0;
        while (m.find()) n++;
        return n;
    }

    // ---- presence checks -----------------------------------------------

    @Test
    void macroFileDeclaresHalf() throws Exception {
        assertTrue(readMacroFile().contains("\\half"),
                "\\half macro must be declared");
    }

    @Test
    void macroFileDeclaresKet() throws Exception {
        assertTrue(readMacroFile().contains("\\ket"),
                "\\ket macro must be declared");
    }

    @Test
    void macroFileDeclaresBra() throws Exception {
        assertTrue(readMacroFile().contains("\\bra"),
                "\\bra macro must be declared");
    }

    @Test
    void macroFileDeclaresTr() throws Exception {
        assertTrue(readMacroFile().contains("\\Tr"),
                "\\Tr macro must be declared");
    }

    @Test
    void macroFileDeclaresDisc() throws Exception {
        assertTrue(readMacroFile().contains("\\Disc"),
                "\\Disc macro must be declared");
    }

    @Test
    void macroFileDeclaresVertex() throws Exception {
        assertTrue(readMacroFile().contains("\\vertex"),
                "\\vertex macro must be declared");
    }

    // ---- count checks --------------------------------------------------

    @Test
    void atLeastTwentyMacrosDeclared() throws Exception {
        long n = countMacros(readMacroFile());
        assertTrue(n >= 20,
                "expected at least 20 macro declarations, found " + n);
    }

    @Test
    void javaMapAndYamlAgreeOnCount() throws Exception {
        long yamlCount = countMacros(readMacroFile());
        int javaCount = KaTeXMacros.count();
        assertEquals(yamlCount, javaCount,
                "YAML declares " + yamlCount + " macros; Java map has " + javaCount);
    }
}