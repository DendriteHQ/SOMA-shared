"""
API contracts for sandbox service.
"""
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class ExecuteBatchRequest(BaseModel):
    """Request to execute a batch of compression tasks."""

    batch_id: str = Field(..., description="Unique identifier for this batch (used for logging)")
    script_presigned_url: str = Field(
        ...,
        description=(
            "Presigned S3 URL (GET) for temporary read access to the miner's challenge script. "
            "The sandbox uses this URL to download the script without direct S3 credentials."
        ),
    )
    challenge_texts: List[str] = Field(..., description="Texts to compress")
    compression_ratios: List[Optional[float]] = Field(
        ..., description="Target compression ratios"
    )
    storage_presigned_urls: List[str] = Field(
        ...,
        description=(
            "Presigned S3 URLs (PUT), one per challenge_text entry. "
            "The sandbox uploads each compressed result to the designated URL "
            "without requiring direct S3 credentials."
        ),
    )
    timeout_per_task: float = Field(..., description="Timeout for each individual task in seconds")
    container_timeout: float = Field(..., description="Global timeout for entire container execution in seconds")


class ExecuteBatchResponse(BaseModel):
    """Response from batch execution."""
    
    success: bool = Field(..., description="Whether execution succeeded")
    batch_id: str = Field(..., description="Batch identifier")
    error: Optional[str] = Field(default=None, description="Error message if entire batch failed")
    task_errors: List[Optional[str]] = Field(
        default_factory=list,
        description="Per-task error messages, one entry per challenge_text. None if the task succeeded, error string if it failed.",
    )
