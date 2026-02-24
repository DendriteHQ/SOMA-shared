from datetime import datetime
from typing import Generic, TypeVar, Literal, List
from pydantic import BaseModel, Field

T = TypeVar("T")

class Signature(BaseModel):
    signer_ss58: str
    nonce: str = Field(description="Unique per request to prevent replay")
    signature: str = Field(description="Base64 signature over canonical bytes")

class SignedEnvelope(BaseModel, Generic[T]):
    payload: T
    sig: Signature