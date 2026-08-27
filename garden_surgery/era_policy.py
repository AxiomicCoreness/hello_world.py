IGNORED_ERAS = ("anthropic_claude", "openai_chatgpt", "andromeda")

def status():
    return {"ignored_eras": list(IGNORED_ERAS), "long_road_replay": False, "pid_wigner_runtime": False, "fusion_canonical": 515, "hyperion_preserved": 516, "deepseek_learning_now": False}
