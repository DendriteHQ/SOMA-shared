from datetime import datetime
from typing import ClassVar, Generic, TypeVar, Literal, List
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")

class UploadSolutionRequest(BaseModel):
    log_omit_fields: ClassVar[frozenset[str]] = frozenset({"solution"})
    miner_hotkey: str
    solution: str

class UploadSolutionResponse(BaseModel):
    ok: bool
    error_msg: str | None = None


class AddOpenRouterApiKeyRequest(BaseModel):
    log_omit_fields: ClassVar[frozenset[str]] = frozenset({"api_key"})
    miner_hotkey: str
    api_key: str


class AddOpenRouterApiKeyResponse(BaseModel):
    ok: bool
    error_msg: str | None = None


class UpdateOpenRouterApiKeyRequest(BaseModel):
    log_omit_fields: ClassVar[frozenset[str]] = frozenset({"api_key"})
    miner_hotkey: str
    api_key: str


class UpdateOpenRouterApiKeyResponse(BaseModel):
    ok: bool
    error_msg: str | None = None


class DeleteOpenRouterApiKeyRequest(BaseModel):
    miner_hotkey: str


class DeleteOpenRouterApiKeyResponse(BaseModel):
    ok: bool
    error_msg: str | None = None


class GetRunLogsRequest(BaseModel):
    miner_hotkey: str
    instance_id: str = Field(min_length=1)
    attempt_no: int = Field(ge=1)
    # Case-insensitive; when omitted, the run from the newest competition is returned.
    competition_name: str | None = Field(default=None, min_length=1)


class CompressorExecLogEntry(BaseModel):
    """One miner-compressor invocation captured by the compression service."""

    # Emitted by the compression service, not by this contract: keep fields it adds later.
    model_config = ConfigDict(extra="allow")

    request_id: str | None = None
    path: str | None = None
    ok: bool | None = None
    compressor_loaded: bool | None = None
    duration_ms: float | None = None
    input_messages: int | None = None
    output_messages: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    error: str | None = None
    traceback: str | None = None


class GetRunLogsResponse(BaseModel):
    # Up to the log cap of the miner's stdout/stderr.
    log_omit_fields: ClassVar[frozenset[str]] = frozenset({"entries"})

    ok: bool
    error_msg: str | None = None
    run_id: int | None = None
    competition_id: int | None = None
    competition_name: str | None = None
    instance_id: str | None = None
    attempt_no: int | None = None
    status: str | None = None
    # The log size is capped (by the sandbox, and again by the platform when returning
    # it) by dropping the oldest entries first. dropped_oldest_entries is what the
    # sandbox counted; entries dropped by the platform are not counted.
    log_truncated: bool = False
    dropped_oldest_entries: int = 0
    entries: list[CompressorExecLogEntry] = Field(default_factory=list)
