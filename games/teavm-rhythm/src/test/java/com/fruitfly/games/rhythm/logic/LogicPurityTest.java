package com.fruitfly.games.rhythm.logic;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.Stream;
import org.junit.jupiter.api.Test;

/** The logic package must stay free of TeaVM/JSO/browser types so it runs on any JVM. */
class LogicPurityTest {

    @Test
    void logicSourcesImportNoTeaVM() throws IOException {
        Path dir = Paths.get("src/main/java/com/fruitfly/games/rhythm/logic");
        assertTrue(Files.isDirectory(dir), dir.toAbsolutePath().toString());
        List<Path> files;
        try (Stream<Path> s = Files.list(dir)) {
            files = s.filter(p -> p.toString().endsWith(".java")).collect(Collectors.toList());
        }
        assertFalse(files.isEmpty());
        for (Path p : files) {
            String src = Files.readString(p);
            assertFalse(src.contains("org.teavm"), p + " imports TeaVM");
            assertFalse(src.contains("com.fruitfly.games.rhythm.web"), p + " depends on web layer");
        }
    }
}
