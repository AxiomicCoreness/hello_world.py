"""Alias only. Does not rename ledger/0336.yaml or ledger/0312.yaml."""

ALIAS = {
    "/anomaly_scan_synthesis_complete_executed": "/fastapi/uvicorn",
    "/integration_hardening_anomaly_scan_sealed": "/fastapi/uvicorn",
    "anomaly": "fastapi/uvicorn",
    "anomoly": "fastapi/uvicorn",
}

KEEP = ("ledger/0336.yaml", "ledger/0312.yaml")


def resolve(event: str) -> str:
    return ALIAS.get(event, event)


def fallback(dep_ok: bool) -> str:
    if dep_ok:
        return "primary"
    return "fastapi/uvicorn"
