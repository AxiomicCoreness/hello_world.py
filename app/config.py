import os


class Settings:
    NAMESPACE = os.getenv("NAMESPACE", "seagate-mimic")
    LEDGER_HEAD = os.getenv("LEDGER_HEAD", "9142")
    PHASE_LOCK = float(os.getenv("PHASE_LOCK", "202.6"))
    BIND_HOST = os.getenv("BIND_HOST", "0.0.0.0")
    BIND_PORT = int(os.getenv("BIND_PORT", "80"))
    MCP_PORT = int(os.getenv("MCP_PORT", "380"))
    MCP_FILLED = os.getenv("MCP_FILLED", "false").lower() == "true"
    GARDEN_SECRET = os.getenv("GARDEN_SECRET", "")
    PHI = 1.618033988749895
    PHI_INV3 = 0.23606797749978967  # ATLAS
    SEAL = 1.509281238970


settings = Settings()
