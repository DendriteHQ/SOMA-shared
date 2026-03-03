from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


def _require_tz(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(
            f"{field_name} must include timezone offset (e.g. 'Z' or '+00:00')"
        )
    return value


class SetBurnRequest(BaseModel):
    is_active: bool
    burn_ratio: float = Field(default=1.0, ge=0, le=1)


class SetBurnResponse(BaseModel):
    ok: bool


class GetBurnStatusRequest(BaseModel):
    """Empty request model for get burn status endpoint"""
    pass


class GetBurnStatusResponse(BaseModel):
    is_active: bool
    burn_ratio: float


class CreateCompetitionRequest(BaseModel):
    competition_name: str
    is_active: bool = False
    upload_starts_at: datetime
    upload_ends_at: datetime
    eval_starts_at: datetime
    eval_ends_at: datetime
    screener_id: int | None = None
    screener_name: str | None = None
    screener_description: str | None = None
    screener_is_active: bool = True
    screener_task_percentage: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator(
        "upload_starts_at",
        "upload_ends_at",
        "eval_starts_at",
        "eval_ends_at",
        mode="after",
    )
    @classmethod
    def _validate_timezone(cls, value: datetime, info):
        return _require_tz(value, info.field_name)


class CreateCompetitionResponse(BaseModel):
    ok: bool
    competition_id: int
    screener_id: int


class UpdateCompetitionRequest(BaseModel):
    competition_id: int
    competition_name: str | None = None
    is_active: bool | None = None
    upload_starts_at: datetime | None = None
    upload_ends_at: datetime | None = None
    eval_starts_at: datetime | None = None
    eval_ends_at: datetime | None = None

    @field_validator(
        "upload_starts_at",
        "upload_ends_at",
        "eval_starts_at",
        "eval_ends_at",
        mode="after",
    )
    @classmethod
    def _validate_timezone(cls, value: datetime | None, info):
        if value is None:
            return value
        return _require_tz(value, info.field_name)


class UpdateCompetitionResponse(BaseModel):
    ok: bool
    competition_id: int


class DeleteCompetitionRequest(BaseModel):
    competition_id: int


class DeleteCompetitionResponse(BaseModel):
    ok: bool


class ListCompetitionsRequest(BaseModel):
    limit: int = Field(default=10, ge=1, le=100)


class CompetitionInfo(BaseModel):
    id: int
    competition_name: str
    is_active: bool
    upload_starts_at: datetime
    upload_ends_at: datetime
    eval_starts_at: datetime
    eval_ends_at: datetime
    created_at: datetime
    updated_at: datetime


class ListCompetitionsResponse(BaseModel):
    ok: bool
    competitions: list[CompetitionInfo]


class CreateScreenerRequest(BaseModel):
    competition_id: int
    screener_name: str
    description: str | None = None
    is_active: bool = True


class CreateScreenerResponse(BaseModel):
    ok: bool
    screener_id: int


class ListScreenersRequest(BaseModel):
    limit: int = Field(default=10, ge=1, le=100)


class ScreenerInfo(BaseModel):
    id: int
    competition_id: int
    screener_name: str
    description: str | None
    is_active: bool


class ListScreenersResponse(BaseModel):
    ok: bool
    screeners: list[ScreenerInfo]


class CreateScreeningChallengesRequest(BaseModel):
    screener_id: int
    challenge_ids: list[int]


class CreateScreeningChallengesResponse(BaseModel):
    ok: bool
    created_count: int
    existing_count: int


class CreateTopMinerRequest(BaseModel):
    ss58: str
    starts_at: datetime
    ends_at: datetime

    @field_validator("starts_at", "ends_at", mode="after")
    @classmethod
    def _validate_timezone(cls, value: datetime, info):
        return _require_tz(value, info.field_name)


class CreateTopMinerResponse(BaseModel):
    ok: bool
    top_miner_id: int


class GetTopMinersRequest(BaseModel):
    limit: int = Field(default=10, ge=1, le=100)


class TopMinerInfo(BaseModel):
    id: int
    ss58: str
    starts_at: datetime
    ends_at: datetime
    created_at: datetime


class GetTopMinersResponse(BaseModel):
    ok: bool
    top_miners: list[TopMinerInfo]


class DeleteTopMinerRequest(BaseModel):
    top_miner_id: int


class DeleteTopMinerResponse(BaseModel):
    ok: bool


class UpdateTopMinerRequest(BaseModel):
    top_miner_id: int
    ss58: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None

    @field_validator("starts_at", "ends_at", mode="after")
    @classmethod
    def _validate_timezone(cls, value: datetime | None, info):
        if value is None:
            return value
        return _require_tz(value, info.field_name)


class UpdateTopMinerResponse(BaseModel):
    ok: bool
    top_miner_id: int
