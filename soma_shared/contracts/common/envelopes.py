from __future__ import annotations
from typing import Generic, TypeVar, Literal
from pydantic import BaseModel, Field

T = TypeVar("T")

class ErrorEnvelope(BaseModel):
    code: str
    message: str
    details: dict | None = None

class ResponseEnvelope(BaseModel, Generic[T]):
    ok: bool = True
    data: T
    request_id: str | None = Field(default=None, description="Trace/correlation id")

class FailEnvelope(BaseModel):
    ok: Literal[False] = False
    error: ErrorEnvelope
    request_id: str | None = None
