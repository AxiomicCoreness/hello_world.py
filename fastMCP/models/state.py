"""State model."""

from pydantic import BaseModel
from enum import Enum

class StateEnum(str, Enum):
    IDLE = "idle"
    BINDING = "binding"
    ACTIVE = "active"
    FILLED = "filled"

class State(BaseModel):
    state: StateEnum = StateEnum.IDLE
    host: str = "127.0.0.1"
    port: int = 8024
