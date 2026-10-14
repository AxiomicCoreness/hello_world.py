package com.fruitfly.brain;

import java.util.LinkedHashMap;
import java.util.Map;

/**
 * 🜁∀ KaTeX macro set — single source of truth ∀🜁
 *
 * <p>Every value is either:
 * <ul>
 *   <li>a {@code String} — macro body with no arguments, or</li>
 *   <li>a {@code [String, Integer]} pair — macro body (using #1, #2)
 *       followed by the number of arguments.</li>
 * </ul>
 *
 * <p>The {@code docs/katex_macros.yaml} and {@code docs/katex_macros.tex}
 * files are generated from this map. The test class
 * {@link KaTeXMacroSetTest} asserts the classpath copy of the YAML
 * contains the six core macros and at least 20 declarations.
 */
public final class KaTeXMacros {

    /** The complete macro set. Insertion order is preserved. */
    public static final Map<String, Object> KATEX_MACROS;
    static {
        Map<String, Object> m = new LinkedHashMap<>();

        // --- Fraction helpers ---
        m.put("\\half",    "\\tfrac{1}{2}");
        m.put("\\third",   "\\tfrac{1}{3}");
        m.put("\\quarter", "\\tfrac{1}{4}");

        // --- Dirac notation ---
        m.put("\\ket",    new Object[]{ "\\left|#1\\right\\rangle", 1 });
        m.put("\\bra",    new Object[]{ "\\left\\langle#1\\right|", 1 });
        m.put("\\braket", new Object[]{ "\\left\\langle#1\\middle|#2\\right\\rangle", 2 });
        m.put("\\ketbra", new Object[]{ "\\left|#1\\right\\rangle\\!\\left\\langle#2\\right|", 2 });
        m.put("\\expect", new Object[]{ "\\left\\langle#1\\right\\rangle", 1 });

        // --- Operators ---
        m.put("\\Tr",     "\\operatorname{Tr}");
        m.put("\\Det",    "\\operatorname{Det}");
        m.put("\\Rank",   "\\operatorname{Rank}");
        m.put("\\diag",   "\\operatorname{diag}");
        m.put("\\vertex", "\\operatorname{vertex}");
        m.put("\\Res",    "\\operatorname{Res}");
        m.put("\\spec",   "\\operatorname{spec}");

        // --- Symbols ---
        m.put("\\Disc",     "\\Delta");
        m.put("\\psitwo",   "\\psi_{2}");
        m.put("\\phiv",     "\\varphi");
        m.put("\\phiinv",   "\\varphi^{-1}");
        m.put("\\phitwo",   "\\varphi^{2}");
        m.put("\\phithree", "\\varphi^{3}");
        m.put("\\phifive",  "\\varphi^{5}");
        m.put("\\phieight", "\\varphi^{8}");
        m.put("\\phinine",  "\\varphi^{9}");

        // --- Derived equations ---
        m.put("\\seedpoly",  "x^{2} - x - 1 = 0");
        m.put("\\seedeq",    "\\Disc = b^{2} - 4ac = 5, \\quad x_{\\vertex} = -\\frac{b}{2a} = \\half");
        m.put("\\darktrace", "\\Tr(\\rho) = 1, \\quad \\Tr(\\rho^{2}) = 1");
        m.put("\\darkeig",   "H\\ket{\\psitwo} = 1 \\cdot \\ket{\\psitwo}");
        m.put("\\darksv",    "\\ket{\\psitwo} = \\frac{1}{\\sqrt{2}} \\begin{pmatrix} 1 \\\\ 0 \\\\ -1 \\end{pmatrix}");
        m.put("\\trimerham", "H = \\begin{pmatrix} 1 & \\phiinv & 0 \\\\ \\phiinv & 2 & \\phiinv \\\\ 0 & \\phiinv & 1 \\end{pmatrix}");

        KATEX_MACROS = java.util.Collections.unmodifiableMap(m);
    }

    private KaTeXMacros() { /* no instances */ }

    /** Number of macros in the set. */
    public static int count() {
        return KATEX_MACROS.size();
    }

    /** True if the given macro name is defined. */
    public static boolean has(String macroName) {
        return KATEX_MACROS.containsKey(macroName);
    }
}                                                                                                                                                                     
