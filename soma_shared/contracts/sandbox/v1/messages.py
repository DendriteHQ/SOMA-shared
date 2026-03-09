"""
API contracts for sandbox service.
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class ExecuteBatchRequest(BaseModel):
    """Request to execute a batch of compression tasks."""
    
    batch_id: str = Field(..., description="Unique identifier for this batch (used for logging)")
    script_s3_key: str = Field(..., description="S3 key for the miner's challenge script")
    challenge_texts: List[str] = Field(..., description="Texts to compress")
    compression_ratios: List[Optional[float]] = Field(
        ..., description="Target compression ratios"
    )
    storage_uuids: List[str] = Field(
        ...,
        description=(
            "S3 storage UUIDs, one per challenge_text entry. "
            "Each compressed result is saved under compressed-texts/{uuid}."
        ),
    )
    timeout_per_task: float = Field(..., description="Timeout for each individual task in seconds")
    container_timeout: float = Field(..., description="Global timeout for entire container execution in seconds")


class ExecuteBatchResponse(BaseModel):
    """Response from batch execution."""
    
    success: bool = Field(..., description="Whether execution succeeded")
    batch_id: str = Field(..., description="Batch identifier")
    error: Optional[str] = Field(default=None, description="Error message if failed")
