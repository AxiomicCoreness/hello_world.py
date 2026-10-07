#!/usr/bin/env python3
from garden_surgery.lead_diagnostic import probe

def test_lead_not_folded():
    p = probe()
    assert p["folded_offline"] is False
    assert p["lead"]["oidc_client_credentials"] is False
    assert p["lead"]["cron_6h"] is False
    assert p["lead"]["restart_from_here"] is False
    assert p["lead"]["alpha_eff"] == 0.0

if __name__ == "__main__":
    test_lead_not_folded()
    print("test_lead_diagnostic: PASS")
