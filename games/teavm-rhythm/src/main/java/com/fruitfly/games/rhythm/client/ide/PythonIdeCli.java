package com.fruitfly.games.rhythm.client.ide;

import com.fruitfly.games.rhythm.client.CliLines;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Offline / local pythonIDE command surface for the TeaVM left CLI.
 * Mirrors {@code pythonIDE/toolkit.py} names (54 capabilities) and
 * {@code pythonIDE/pointer_2300.py} labels. No live Python in the browser —
 * when the loopback bridge is up, {@code /py call …} is forwarded and the
 * bridge runs the real toolkit with traceback; offline, this class lists
 * capabilities and formats useful errors / traceback-shaped lines into chat.
 */
public final class PythonIdeCli {
    /** Capability names aligned with pythonIDE/toolkit.py (honest 54). */
    public static final String[] CAPABILITIES = {
            "golden_ratio", "fibonacci", "phi_power", "lindelof_bound", "uncertainty_product",
            "purity_calc", "entropy_calc", "commutator", "trace_preservation", "nullify_ban_check",
            "conjunction_coherence", "perihelion_correction", "retrocausal_kernel", "chronal_cement",
            "rainbow_armor", "lenticular_damping", "future_scan", "temporal_anchor",
            "merkle_root", "seal_add", "seal_get", "witness_verify", "hmac_sign", "ledger_length",
            "integrity_hash", "fingerprint", "rotation_count", "sovereign_signature",
            "fano_plane", "golden_sphere", "harmonic_shells", "e8_lattice", "exotic_spheres",
            "selene_forge", "u_orisma", "golden_rectangles",
            "fleet_capacity", "missile_phase_lock", "autonomous_release", "zero_workload",
            "pid_error", "coherence_target", "soul_cannon", "void_integral",
            "dagger_catalogue", "operator_freq", "operator_integrity", "grok_client",
            "deepseek_client", "sovereign_dispatch",
            "soft_max", "delta_lemma", "rk4_step", "health"
    };

    private PythonIdeCli() {
    }

    /** True for lines the CLI should treat as pythonIDE commands. */
    public static boolean isIdeLine(String raw) {
        if (raw == null) {
            return false;
        }
        String t = raw.trim();
        if (t.isEmpty()) {
            return false;
        }
        String lower = t.toLowerCase();
        return lower.startsWith("/py")
                || lower.startsWith("/ide")
                || lower.startsWith("py ")
                || lower.equals("py")
                || lower.startsWith("ide ")
                || lower.equals("ide")
                || lower.equals("/pythonide")
                || lower.startsWith("/pythonide ")
                || lower.equals("/deepinfer")
                || lower.startsWith("/deepinfer ")
                || lower.equals("deepinfer")
                || lower.startsWith("deepinfer ")
                || lower.equals("/katex")
                || lower.startsWith("/katex ")
                || lower.equals("katex")
                || lower.startsWith("katex ");
    }

    /**
     * Strip the leading verb ({@code /py}, {@code py}, {@code /ide}, …) and
     * return the remainder (may be empty).
     */
    public static String stripVerb(String raw) {
        String t = raw == null ? "" : raw.trim();
        String[] verbs = {
            "/pythonide", "/py", "/ide", "pythonide", "py", "ide",
            "/deepinfer", "deepinfer", "/katex", "katex"
        };
        String lower = t.toLowerCase();
        for (String v : verbs) {
            if (lower.equals(v)) {
                if ("/deepinfer".equals(v) || "deepinfer".equals(v)) {
                    return "deepinfer";
                }
                if ("/katex".equals(v) || "katex".equals(v)) {
                    return "katex";
                }
                return "";
            }
            if (lower.startsWith(v + " ")) {
                String rest = t.substring(v.length()).trim();
                if ("/deepinfer".equals(v) || "deepinfer".equals(v)) {
                    return ("deepinfer " + rest).trim();
                }
                if ("/katex".equals(v) || "katex".equals(v)) {
                    return ("katex " + rest).trim();
                }
                return rest;
            }
        }
        return t;
    }

    /**
     * Handle one IDE line offline. Returns tagged chat lines (System / Engine / Traceback).
     * Does not execute arbitrary Python — call/list/help/pointer only.
     */
    public static List<String> handleOffline(String raw) {
        List<String> out = new ArrayList<>();
        if (!isIdeLine(raw)) {
            return out;
        }
        String rest = stripVerb(raw);
        if (rest.isEmpty() || "help".equalsIgnoreCase(rest) || "?".equals(rest)) {
            help(out);
            return out;
        }
        String[] parts = rest.split("\\s+", 3);
        String cmd = parts[0].toLowerCase();
        switch (cmd) {
            case "help":
            case "?":
                help(out);
                break;
            case "list":
            case "ls":
                out.add(CliLines.format(CliLines.KIND_ENGINE,
                        "pythonIDE toolkit · " + CAPABILITIES.length + " capabilities"));
                out.add(CliLines.format(CliLines.KIND_ENGINE, String.join(", ", CAPABILITIES)));
                out.add(CliLines.format(CliLines.KIND_SYSTEM,
                        "bridge: /py call <name> [args…] · offline lists only"));
                break;
            case "pointer":
            case "2300":
                pointer(out);
                break;
            case "deepinfer":
            case "di":
                deepinferOffline(out, parts.length > 1 ? parts[1] : "");
                break;
            case "katex":
            case "katex_test":
            case "katexmacrosettest":
            case "macros":
                katexOffline(out);
                break;
            case "call":
            case "run":
                if (parts.length < 2) {
                    traceback(out, "PythonIdeCli.call", "TypeError",
                            "call requires capability name",
                            "Usage: /py call <name> [arg…]");
                } else {
                    String name = parts[1];
                    if (!known(name)) {
                        traceback(out, "pythonIDE.toolkit.call", "CapabilityError",
                                "unknown capability: " + name,
                                "hint: /py list");
                    } else {
                        out.add(CliLines.format(CliLines.KIND_SYSTEM,
                                "offline stub · capability '" + name
                                        + "' needs ws://127.0.0.1:6680/cli bridge for live toolkit"));
                        out.add(CliLines.format(CliLines.KIND_ENGINE,
                                "queued: call " + name
                                        + (parts.length > 2 ? " " + parts[2] : "")));
                    }
                }
                break;
            default:
                if (known(cmd)) {
                    out.add(CliLines.format(CliLines.KIND_SYSTEM,
                            "offline stub · use '/py call " + cmd + "' when bridge is up"));
                } else {
                    traceback(out, "PythonIdeCli.handle", "ValueError",
                            "unknown ide command: " + cmd,
                            "try: /py help | /py list | /py call <cap> | /py pointer | /py deepinfer | /py katex");
                }
                break;
        }
        return Collections.unmodifiableList(out);
    }

    public static boolean known(String name) {
        if (name == null) {
            return false;
        }
        for (String c : CAPABILITIES) {
            if (c.equals(name)) {
                return true;
            }
        }
        return false;
    }

    /** Format a traceback-shaped block for chat history. */
    public static List<String> formatTraceback(String where, String excType, String message,
            String... extras) {
        List<String> out = new ArrayList<>();
        traceback(out, where, excType, message, extras);
        return Collections.unmodifiableList(out);
    }

    private static void help(List<String> out) {
        out.add(CliLines.format(CliLines.KIND_SYSTEM,
                "pythonIDE CLI · align pythonIDE/toolkit.py + pointer_2300"));
        out.add(CliLines.format(CliLines.KIND_ENGINE,
                "commands: /py help | /py list | /py call <cap> [args] | /py pointer"));
        out.add(CliLines.format(CliLines.KIND_ENGINE,
                "demos: /py deepinfer | /py katex (KaTeXMacroSetTest) · Traceback on fail"));
        out.add(CliLines.format(CliLines.KIND_ENGINE,
                "local/CI dial: " + CliLines.LOOPBACK_WS + " · errors return Traceback lines"));
        out.add(CliLines.format(CliLines.KIND_SYSTEM,
                "NO_LEDGER_WRITE · Cosmic Alignment loopback only"));
    }

    private static void pointer(List<String> out) {
        out.add(CliLines.format(CliLines.KIND_ENGINE, "pointer 2300 → Context Layer 314"));
        out.add(CliLines.format(CliLines.KIND_ENGINE,
                "domain GARDEN.LAYER314.ANCHOR.v1 · teavm_rhythm=games/teavm-rhythm/"));
        out.add(CliLines.format(CliLines.KIND_ENGINE,
                "author Clarke Yoursa Tee · float_compare=math.isclose · full 64-hex digests"));
        out.add(CliLines.format(CliLines.KIND_SYSTEM,
                "live payload: python -m pythonIDE.pointer_2300 (repo root)"));
    }

    private static void deepinferOffline(List<String> out, String sub) {
        out.add(CliLines.format(CliLines.KIND_SYSTEM,
                "offline stub · deepinfer needs ws://127.0.0.1:6680/cli bridge"));
        out.add(CliLines.format(CliLines.KIND_ENGINE,
                "queued: /py deepinfer"
                        + (sub == null || sub.isEmpty() ? "" : " " + sub)
                        + " · engine/deepinfer_accelerator.py"));
        out.add(CliLines.format(CliLines.KIND_ENGINE,
                "live: status | probe | complete [prompt] · Traceback on import miss"));
    }

    private static void katexOffline(List<String> out) {
        out.add(CliLines.format(CliLines.KIND_SYSTEM,
                "offline stub · KaTeXMacroSetTest needs bridge (mvn or python mirror)"));
        out.add(CliLines.format(CliLines.KIND_ENGINE,
                "queued: mvn test -Dtest=KaTeXMacroSetTest · docs/katex_macros.yaml"));
        out.add(CliLines.format(CliLines.KIND_ENGINE,
                "tests: strictTreeIsValid · darkLambdaIsPresent · Traceback on fail"));
    }

    private static void traceback(List<String> out, String where, String excType, String message,
            String... extras) {
        out.add(CliLines.format(CliLines.KIND_TRACEBACK, "Traceback (most recent call last):"));
        out.add(CliLines.format(CliLines.KIND_TRACEBACK, "  File \"" + where + "\", line 1, in <cli>"));
        out.add(CliLines.format(CliLines.KIND_TRACEBACK, excType + ": " + message));
        if (extras != null) {
            for (String e : extras) {
                if (e != null && !e.isEmpty()) {
                    out.add(CliLines.format(CliLines.KIND_SYSTEM, e));
                }
            }
        }
    }
}
