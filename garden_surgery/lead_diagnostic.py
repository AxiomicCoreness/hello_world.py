"""Lead diagnostic — four bans are first-class, not offline-folded."""

BANS = {
    "oidc_client_credentials": False,
    "cron_6h": False,
    "restart_from_here": False,
    "alpha_eff": 0.0,
}


def probe():
    return {
        "lead": BANS,
        "folded_offline": False,
        "fusion_canonical": 515,
        "hyperion_preserved": 516,
        "deepseek_training": False,
    }
