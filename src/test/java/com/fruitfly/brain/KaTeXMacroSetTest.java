package com.fruitfly.brain;

import org.junit.jupiter.api.Test;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;

import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * Strict KaTeX domain-tree tests. Classpath resource {@code katex_macros.yaml}
 * is copied from {@code docs/} by pom testResources. Stokes micro is separate.
 */
class KaTeXMacroSetTest {

    private static final String RESOURCE = "katex_macros.yaml";

    @Test
    void strictTreeIsValid() throws Exception {
        try (InputStream in = getClass().getClassLoader().getResourceAsStream(RESOURCE)) {
            assertNotNull(in, RESOURCE + " must exist on the classpath");
            KaTeXTreeValidator.validateStrictTree(in);
        }
    }

    @Test
    void darkLambdaIsPresent() throws Exception {
        try (InputStream in = getClass().getClassLoader().getResourceAsStream(RESOURCE)) {
            assertNotNull(in, RESOURCE + " must exist on the classpath");
            String content = new String(in.readAllBytes(), StandardCharsets.UTF_8);
            assertTrue(
                    content.contains("\"\\\\darklambda\"") || content.contains("\"\\darklambda\""),
                    "\\darklambda must be present");
            assertTrue(content.contains("garden:"), "garden domain must be present");
        }
    }
}
