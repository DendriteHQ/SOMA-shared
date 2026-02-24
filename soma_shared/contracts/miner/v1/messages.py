from datetime import datetime
from typing import Generic, TypeVar, Literal, List
from pydantic import BaseModel, Field

T = TypeVar("T")

class UploadSolutionRequest(BaseModel):
    miner_hotkey: str
    solution: str

class UploadSolutionResponse(BaseModel):
    ok: bool
    error_msg: str | None = None
