from scripts.hook_branch_policy import (
    hook_policy,
    will_update_all_branches_over_time,
)


def test_hook_does_not_mass_update():
    assert will_update_all_branches_over_time() is False
    body = hook_policy()
    assert body["mcp_filled"] is False
    assert body["mass_update_historical"] is False
    assert body["bind_0000"] is False
    assert body["dual_asgi"] == "127.0.0.1:8024"
    assert "main" in body["allowed_git_targets"]
    assert "deepseek" in body["allowed_git_targets"]
