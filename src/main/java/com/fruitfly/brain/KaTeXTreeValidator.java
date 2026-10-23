package com.fruitfly.brain;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Strict KaTeX domain-tree validator for {@code katex_macros.yaml}.
 *
 * <p>Parses {@code katex.macros.{math,garden,physics}} domains from raw lines
 * (no YAML library). Enforces uniqueness across domains, rejects macros at
 * domain-less {@code root}, rejects self-reference, and DFS-detects cycles
 * among known macro keys. Stokes micro files are out of scope.
 */
public final class KaTeXTreeValidator {

    /** Key + string expansion, or key + first element of {@code ["expansion", N]}. */
    private static final Pattern MACRO_PATTERN = Pattern.compile(
            "^\\s*\"(\\\\{1,2}[A-Za-z]+)\"\\s*:\\s*(?:\"([^\"]*)\"|\\[\\s*\"([^\"]*)\")"
    );

    private static final Pattern REF_PATTERN = Pattern.compile("(\\\\{1,2}[A-Za-z]+)");

    private static final Pattern DOMAIN_PATTERN = Pattern.compile("^([a-z]+):$");

    private KaTeXTreeValidator() {
    }

    /**
     * Validates the strict tree structure and dependency graph.
     *
     * @param yamlStream the katex_macros.yaml stream (classpath or docs/)
     * @throws IllegalStateException if the tree is malformed or cyclic
     */
    public static void validateStrictTree(InputStream yamlStream) throws Exception {
        Map<String, String> macroMap = new HashMap<>();
        Map<String, String> domainOf = new HashMap<>();
        List<String[]> pending = new ArrayList<>();

        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(yamlStream, StandardCharsets.UTF_8))) {
            String line;
            String currentDomain = "root";

            while ((line = reader.readLine()) != null) {
                String trimmed = line.trim();
                if (trimmed.isEmpty() || trimmed.startsWith("#")
                        || trimmed.equals("katex:") || trimmed.equals("macros:")) {
                    continue;
                }

                Matcher domain = DOMAIN_PATTERN.matcher(trimmed);
                if (domain.matches()) {
                    currentDomain = domain.group(1);
                    continue;
                }

                Matcher m = MACRO_PATTERN.matcher(line);
                if (!m.find()) {
                    continue;
                }
                String macroKey = normalizeTeXName(m.group(1));
                String expansion = m.group(2) != null ? m.group(2) : m.group(3);
                if (expansion == null) {
                    throw new IllegalStateException("Missing expansion for " + macroKey);
                }
                if ("root".equals(currentDomain)) {
                    throw new IllegalStateException(
                            "Macro outside domain (math|garden|physics): " + macroKey);
                }
                if (macroMap.containsKey(macroKey)) {
                    throw new IllegalStateException(
                            "Duplicate macro definition: " + macroKey
                                    + " in domain " + currentDomain
                                    + " (already in " + domainOf.get(macroKey) + ")");
                }
                macroMap.put(macroKey, expansion);
                domainOf.put(macroKey, currentDomain);
                pending.add(new String[]{macroKey, expansion});
            }
        }

        Map<String, List<String>> dependencyGraph = new HashMap<>();
        for (String[] pair : pending) {
            String macroKey = pair[0];
            String expansion = pair[1];
            List<String> deps = new ArrayList<>();
            Matcher refMatcher = REF_PATTERN.matcher(expansion);
            while (refMatcher.find()) {
                String dep = normalizeTeXName(refMatcher.group(1));
                if (dep.equals(macroKey)) {
                    throw new IllegalStateException(
                            "Self-referential macro expansion: " + macroKey);
                }
                if (macroMap.containsKey(dep)) {
                    deps.add(dep);
                }
            }
            dependencyGraph.put(macroKey, deps);
        }

        Set<String> visited = new HashSet<>();
        Set<String> recursionStack = new HashSet<>();
        for (String node : dependencyGraph.keySet()) {
            if (detectCycle(node, dependencyGraph, visited, recursionStack)) {
                throw new IllegalStateException(
                        "Cyclic macro dependency detected involving: " + node);
            }
        }

        System.out.println(
                "Strict KaTeX Tree Validated. Total Macros: " + macroMap.size());
    }

    /** Collapse raw {@code \\name} / {@code \name} to canonical {@code \name}. */
    static String normalizeTeXName(String raw) {
        String letters = raw.replace("\\", "");
        return "\\" + letters;
    }

    private static boolean detectCycle(
            String node,
            Map<String, List<String>> graph,
            Set<String> visited,
            Set<String> stack) {
        if (stack.contains(node)) {
            return true;
        }
        if (visited.contains(node)) {
            return false;
        }
        visited.add(node);
        stack.add(node);
        for (String neighbor : graph.getOrDefault(node, Collections.emptyList())) {
            if (detectCycle(neighbor, graph, visited, stack)) {
                return true;
            }
        }
        stack.remove(node);
        return false;
    }
}
