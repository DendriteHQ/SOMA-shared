"""
API contracts for sandbox service.
"""
from __future__ import annotations

from typing import Any, List, Optional
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
    execution_times: List[Optional[float]] = Field(
        default_factory=list,
        description="Per-task execution times in seconds, one entry per challenge_text. None if the task failed or time is unavailable.",
    )


class CompactBenchRunTaskRequest(BaseModel):
    """Single benchmark execution request for the compact-bench backend."""

    benchmark: str = Field(..., description="Benchmark dataset identifier.")
    instance_id: str = Field(..., description="Concrete benchmark instance identifier.")
    run_id: int = Field(..., description="Run identifier for this execution.")
    script_presigned_url: str = Field(
        ...,
        description=(
            "Presigned S3 URL (GET) used to download the miner code that should be injected into the "
            "Somarizer/OpenClaw plugin for this task."
        ),
    )
    trajectory_presigned_url: str | None = Field(
        default=None,
        description=(
            "Presigned S3 URL (PUT) used to upload the agent trajectory (JSONL) captured during "
            "this run. The sandbox uploads the trajectory to the designated URL without requiring "
            "direct S3 credentials. When omitted, trajectory upload is skipped."
        ),
    )
    compression_logs_presigned_url: str | None = Field(
        default=None,
        description=(
            "Presigned S3 URL (PUT) used to upload the compressor execution log captured during "
            "this run: JSONL with one entry per miner-compressor invocation on the compression "
            "service's /transform endpoint (timing, captured stdout/stderr, errors). The sandbox "
            "uploads it without requiring direct S3 credentials. When omitted, upload is skipped."
        ),
    )
    agent_name: str = Field(default="openclaw", description="Compact-bench runtime backend name.")
    benchmark_type: str = Field(default="swebench_verified", description="Benchmark type: swebench_verified, swe_explorer_explore, or swe_explorer_edit.")
    model: str | None = Field(default=None, description="Optional LLM model override.")
    openclaw_timeout: int | None = Field(default=1800, description="Optional timeout override for OpenClaw execution in seconds.")
    openclaw_disable_somarizer: bool = Field(default=False)
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Opaque task metadata echoed back in the response for caller correlation.",
    )


class CompactBenchRunTaskResponse(BaseModel):
    """Per-task execution result for the compact-bench backend."""
    success: bool = Field(..., description="Whether request was accepted successfully for execution.")


class CompactBenchReportRequest(BaseModel):
    """Per-task execution result for the compact-bench backend."""

    run_id: int = Field(..., description="Run identifier for this execution.")
    ok_status: bool = Field(..., description="Compact-bench/OpenClaw runtime status.")
    error: str | None = Field(default=None, description="Task-level error message.")
    execution_time_seconds: float | None = Field(
        default=None,
        description="Observed end-to-end runtime for the benchmark solve command.",
    )
    total_tokens: int | None = Field(
        default=None,
        description="Total token count reported by the benchmark runtime for this run.",
    )
    input_tokens: int | None = Field(
        default=None,
        description="Input prompt tokens excluding cache-read tokens.",
    )
    cached_input_tokens: int | None = Field(
        default=None,
        description="Input tokens served from cache reads.",
    )
    output_tokens: int | None = Field(
        default=None,
        description="Output/completion tokens.",
    )
    agent_steps: int | None = Field(
        default=None,
        description="Best-effort count of agent steps observed during execution.",
    )
    trajectory_upload_status: bool | None = Field(
        default=None,
        description=(
            "Whether the agent trajectory was uploaded to the presigned trajectory URL. "
            "True when the upload succeeded, False when it was attempted or expected but failed "
            "(including a missing trajectory file), None when no trajectory_presigned_url was provided."
        ),
    )
    compression_logs_upload_status: bool | None = Field(
        default=None,
        description=(
            "Whether the compression-service execution logs were uploaded to the presigned URL. "
            "True when the upload succeeded, False when it was attempted or expected but failed "
            "(including a missing log file), None when no compression_logs_presigned_url was provided."
        ),
    )
    patch_capture_status: bool = Field(..., description="Whether the patch capture was successful and included in the report.")
    patch_diff: str | None = Field(
        default=None,
        description=(
            "Unified diff string representing the changes made by the agent, generated by compact-bench/OpenClaw's patch capture. "
            "This payload is returned directly in the callback contract and may be None if the patch capture failed or if no changes were made."
        ),
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Opaque execution metadata for debugging and downstream processing.",
    )

class CompactBenchReportResponse(BaseModel):
    """Per-task execution result for the compact-bench backend."""
    success: bool = Field(..., description="Whether request was accepted successfully for execution.")

class ApiGatewayProxyPayload(BaseModel):
    method: str = Field(default="POST", description="HTTP method for upstream request.")
    url: str = Field(..., description="Upstream URL to proxy to.")
    headers: dict[str, str] = Field(default_factory=dict, description="Upstream request headers.")
    timeout_seconds: float = Field(default=30.0, description="Per-request timeout for upstream call.")
    body: dict[str, Any] | list[Any] | str | None = Field(
        default=None,
        description="Inline request payload.",
    )


class ApiGatewayRequest(BaseModel):
    """Generic API Gateway request wrapper."""
    body: ApiGatewayProxyPayload = Field(..., description="Typed proxy request payload.")
    run_id: int = Field(..., description="Run identifier for this execution, used for logging and correlation.")
    
class ApiGatewayResponse(BaseModel):
    """Generic API Gateway response wrapper."""
    success: bool = Field(..., description="Whether the request was processed successfully.")
    error: Optional[str] = Field(default=None, description="Error message if processing failed.")
    status_code: int | None = Field(default=None, description="Upstream HTTP status code when available.")
    headers: dict[str, str] | None = Field(default=None, description="Selected upstream response headers.")
    body: str | None = Field(default=None, description="Raw response payload from upstream, if applicable.")
