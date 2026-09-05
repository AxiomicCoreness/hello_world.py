# Pydantic v2 validators (Garden note)

9182 / 9183 YAML and BIN layers are not rewritten by this file.

## Do not use v1 `@validator` on new Garden models

Pydantic v2 deprecates `@validator` and `@root_validator`.

Use:

- `@field_validator("field", mode="after")` for one field
- `@model_validator(mode="after")` for cross-field checks
- `ValidationInfo.data` instead of the old `values` dict
- `Field(validate_default=True)` when a default must run through the validator

```python
from pydantic import BaseModel, Field, ValidationInfo, field_validator

class PhaseLockModel(BaseModel):
    phase_lock: float = Field(default=202.6)
    north_star_hz: float = Field(default=71.975)
    dual_asgi: str = Field(default="127.0.0.1:8024")

    @field_validator("dual_asgi")
    @classmethod
    def loopback_only(cls, v: str) -> str:
        if v.startswith("0.0.0.0") or v.startswith(":"):
            raise ValueError("refuse wildcard — Dual ASGI is 127.0.0.1:8024")
        return v

    @field_validator("phase_lock")
    @classmethod
    def lock_token(cls, v: float, info: ValidationInfo) -> float:
        if abs(v - 202.6) > 1e-9:
            raise ValueError("phase_lock token is 202.6")
        return v
```

`fastMCP/models/envelope.py` has no `@validator` today. Leave it. Do not back-port v1 signatures.

## BIN layers — append a new layer, do not rewrite bytes

Order stays:

1. `sovereign_core.bin`
2. `ledger_tip.bin`
3. `octonian_relay.bin`
4. `adai_annihilator.bin`

A phase_lock change inside `sovereign_core.bin` needs a **new** layer file plus a **new** ledger index. It does not edit 9167, 9182, or 9183 in place.
