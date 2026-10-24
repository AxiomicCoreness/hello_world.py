package com.fruitfly.games.rhythm.client.llm;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import com.fruitfly.games.rhythm.client.ide.PythonIdeCli;
import org.junit.jupiter.api.Test;

class LlmCliTest {
    @Test
    void recognisesVerb() {
        assertTrue(LlmCli.isLlmLine("/llm hi"));
        assertTrue(LlmCli.isLlmLine("  /LLM   hi"));
        assertTrue(LlmCli.isLlmLine("/llm"));
        assertFalse(LlmCli.isLlmLine("/llmx"));
        assertFalse(LlmCli.isLlmLine("/py call golden_ratio"));
        assertFalse(PythonIdeCli.isIdeLine("/llm hi"), "llm is not routed through pythonIDE");
    }

    @Test
    void wireCarriesSnapshotAndFeedback() {
        String w = LlmCli.wire("/llm what are\nthe lanes doing?", "{\"v\":1}", "{\"kind\":\"traceback\"}");
        assertEquals("/llm what are the lanes doing?\n#neuro {\"v\":1}\n#feedback {\"kind\":\"traceback\"}", w);
        assertEquals("/llm hi", LlmCli.wire("/llm hi", null, ""));
    }

    @Test
    void offlineLineIsSystem() {
        assertTrue(LlmCli.offlineLine().startsWith("[System] llm offline"));
    }
}
