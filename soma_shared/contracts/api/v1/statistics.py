from __future__ import annotations
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, List

class GetValidationStatusRequest(BaseModel):
    miner_hotkey: str
    
class GetValidationStatusResponse(BaseModel):
    status: Literal["not_registered", "registered", "validating", "validated", "failed"]
    validation_start_ts: datetime | None = None
    validated_cases: int = 0 # How many cases were already validated
    total_cases: int = 0     # Total number of cases assigned
    successful_cases: int = 0 # How many cases were successfully validated
    currently_validated_by: List
    