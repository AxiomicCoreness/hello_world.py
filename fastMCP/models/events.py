"""Event model."""

from pydantic import BaseModel
from datetime import datetime

class Event(BaseModel):
    entry: int
    event: str
    hash: str
    timestamp: datetime = datetime.now()
