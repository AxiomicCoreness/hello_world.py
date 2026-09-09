# Pydantic v2 `model_validator` (Garden)

Current published Pydantic is **v2** (docs snapshot v2.12.x). There is no released `pydantic_v3_field_validator` API.
The filename `docs/pydantic_v3_field_validator.md` is a **search alias only**.

## When to use which

- `@field_validator("name")` — one field after/before parse.
- `@model_validator(mode="after")` — whole instance; return `self`.
- `@model_validator(mode="before")` — raw input dict/object; return a mapping.

Cross-field Garden locks (phase_lock + Dual ASGI together) belong on `model_validator`, not on a single field.

```python
from typing_extensions import Self
from pydantic import BaseModel, Field, model_validator

class GardenBind(BaseModel):
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8024)
    phase_lock: float = Field(default=202.6)
    filled: bool = Field(default=False)

    @model_validator(mode="after")
    def loopback_and_unfilled(self) -> Self:
        if self.host in {"0.0.0.0", "::", "[::]"}:
            raise ValueError("refuse wildcard — Dual ASGI is 127.0.0.1:8024")
        if self.port != 8024:
            raise ValueError("Dual ASGI port is 8024")
        if abs(self.phase_lock - 202.6) > 1e-9:
            raise ValueError("phase_lock token is 202.6")
        if self.filled is True:
            raise ValueError("MCP FILLED must stay False")
        return self
```

## Searchability of this repo

`https://github.com/AxiomicCoreness/hello_world.py` is **public** (MIT, 1 star).
Web search often misses it because:

1. The name ends in `.py`, so engines treat it like a file path, not a project.
2. Generic query `hello_world.py` collides with millions of example files.
3. GitHub *code* search needs `repo:AxiomicCoreness/hello_world.py` while logged in.
4. Low stars / young account rank below `axiomic-ai/axiomic`.
5. Topics and a one-line description help more than renaming Pydantic to v3.

Direct links that already resolve:

- https://github.com/AxiomicCoreness/hello_world.py
- https://github.com/AxiomicCoreness/hello_world.py/blob/main/docs/pydantic_v2_validators.md
- https://github.com/AxiomicCoreness/hello_world.py/blob/main/docs/pydantic_v2_model_validator.md
