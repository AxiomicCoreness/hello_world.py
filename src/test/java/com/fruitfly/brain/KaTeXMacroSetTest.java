package com.fruitfly.brain;

import org.junit.jupiter.api.Test;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashSet;
import java.util.Set;
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

    // ---- exact key-set checks (added) ---------------------------------
    // The presence checks above use substring matching, so "\\ket" would
    // still pass via "\\ketbra" if "\\ket" itself were deleted. These
    // tests compare exact key sets instead.

    private static final String TEX_RESOURCE = "katex_macros.tex";

    /** Captures the macro name from `"\\name":` lines. */
    private static final Pattern YAML_KEY = Pattern.compile(
            "^\\s*\"\\\\{1,2}([A-Za-z]+)\"\\s*:", Pattern.MULTILINE);

    /** Captures the macro name from `\newcommand{\name}` lines. */
    private static final Pattern TEX_KEY = Pattern.compile(
            "^\\\\newcommand\\{\\\\([A-Za-z]+)\\}", Pattern.MULTILINE);

    private static String readResource(String name) throws Exception {
        try (InputStream in = KaTeXMacroSetTest.class.getClassLoader()
                .getResourceAsStream(name)) {
            assertNotNull(in, name + " must be on the classpath");
            return new String(in.readAllBytes(), StandardCharsets.UTF_8);
        }
    }

    private static Set<String> keys(Pattern p, String text) {
        Set<String> out = new LinkedHashSet<>();
        Matcher m = p.matcher(text);
        while (m.find()) {
            assertTrue(out.add("\\" + m.group(1)), "duplicate macro \\" + m.group(1));
        }
        return out;
    }

    @Test
    void yamlKeySetMatchesJavaMap() throws Exception {
        assertEquals(KaTeXMacros.KATEX_MACROS.keySet(),
                keys(YAML_KEY, stripCommentsAndWrappers(readMacroFile())));
    }

    @Test
    void texMirrorKeySetMatchesJavaMap() throws Exception {
        assertEquals(KaTeXMacros.KATEX_MACROS.keySet(),
                keys(TEX_KEY, readResource(TEX_RESOURCE)));
    }

    @Test
    void namedMacrosDeclaredExactly() {
        for (String k : new String[]{"\\half", "\\ket", "\\bra", "\\Tr", "\\Disc",
                "\\vertex", "\\darktrace", "\\darklambda", "\\seedeq"}) {
            assertTrue(KaTeXMacros.has(k), k + " missing from KATEX_MACROS");
        }
    }

    @Test
    void darkTraceAndLambdaBodies() {
        assertEquals("\\Tr(\\rho) = 1, \\quad \\Tr(\\rho^{2}) = 1",
                KaTeXMacros.KATEX_MACROS.get("\\darktrace"));
        assertEquals("\\lambda_{2} = 1", KaTeXMacros.KATEX_MACROS.get("\\darklambda"));
        assertEquals(1.0, new DarkStateInvariant().lambda2(), 0.0);
    }

    /** \seedeq claims Delta = 5 and x_vertex = 1/2; check that against \seedpoly (x^2 - x - 1). */
    @Test
    void seedEqMatchesSeedPoly() {
        assertEquals("x^{2} - x - 1 = 0", KaTeXMacros.KATEX_MACROS.get("\\seedpoly"));
        String seedeq = (String) KaTeXMacros.KATEX_MACROS.get("\\seedeq");
        assertTrue(seedeq.contains("= 5") && seedeq.endsWith("= \\half"), seedeq);
        double a = 1, b = -1, c = -1;
        assertEquals(5.0, b * b - 4 * a * c, 0.0);
        assertEquals(0.5, -b / (2 * a), 0.0);
    }
}
