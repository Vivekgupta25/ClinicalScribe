from pydantic import BaseModel
from typing import Literal


class Medication(BaseModel):
    name: str
    dose: str = "NOT_DOCUMENTED"
    route: str = "NOT_DOCUMENTED"
    frequency: str = "NOT_DOCUMENTED"
    duration: str = "NOT_DOCUMENTED"
    status: Literal["new", "continued", "stopped", "changed", "unknown"] = "unknown"
