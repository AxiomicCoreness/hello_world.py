from quantum.deepseek_mesh import terminal


def test_autonomous_runner_is_bounded_and_ordered(monkeypatch):
    calls = []

    class Metrics:
        def __init__(self):
            self.coherence = 0.99
            self.pid_error = 0.001
            self.phi_phase = 0.0

        def update(self, elapsed):
            calls.append(("update", elapsed))
            self.coherence = 0.99 + elapsed / 100
            self.pid_error = 0.0003
            self.phi_phase = elapsed
            return elapsed >= 0.2

    class Envelope:
        def compute(self, coherence):
            calls.append(("compute", coherence))
            return coherence

    class State:
        def set(self, key, value):
            calls.append(("set", key, value))

    class Engram:
        def integrity_hash(self):
            return "test-integrity"

        def display(self):
            calls.append(("display",))

        def run_closed_loop(self):
            calls.append(("closed-loop",))

    monkeypatch.setattr(terminal, "load_hyperion_state", lambda: calls.append(("load",)))
    monkeypatch.setattr(terminal, "SovereignMetrics", Metrics)
    monkeypatch.setattr(terminal, "UprhoEnvelope", Envelope)
    monkeypatch.setattr(terminal, "STATE", State())
    monkeypatch.setattr(
        terminal, "save_hyperion_state", lambda force=False: calls.append(("save", force)) or True
    )
    monkeypatch.setattr(terminal, "Engram5Layer", Engram)
    monkeypatch.setattr(terminal, "interactive_menu", lambda: calls.append(("menu",)))
    monkeypatch.setattr(terminal, "run_server", lambda *_: calls.append(("server",)))

    report = terminal.run_autonomous_and_automated()

    assert [call[1] for call in calls if call[0] == "update"] == [0.0, 0.1, 0.2]
    assert calls.index(("load",)) < calls.index(("compute", 0.992))
    assert calls.index(("save", True)) < calls.index(("display",))
    assert calls.index(("display",)) < calls.index(("closed-loop",))
    assert not any(call[0] in {"menu", "server"} for call in calls)
    assert report["ok"] is True
    assert report["locked_at"] == 0.2
    assert report["engram_integrity"] == "test-integrity"


def test_main_defaults_to_autonomous_mode(monkeypatch):
    calls = []
    monkeypatch.setattr(terminal.sys, "argv", ["terminal.py"])
    monkeypatch.setattr(
        terminal, "run_autonomous_and_automated", lambda: calls.append("autonomous")
    )

    terminal.main()

    assert calls == ["autonomous"]


def test_main_keeps_interactive_mode_opt_in(monkeypatch):
    calls = []
    monkeypatch.setattr(terminal.sys, "argv", ["terminal.py", "--interactive"])
    monkeypatch.setattr(terminal, "load_hyperion_state", lambda: calls.append("load"))
    monkeypatch.setattr(terminal, "interactive_menu", lambda: calls.append("menu"))
    monkeypatch.setattr(
        terminal, "run_autonomous_and_automated", lambda: calls.append("autonomous")
    )

    terminal.main()

    assert calls == ["load", "menu"]