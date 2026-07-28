from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class CurrentCompetitionTimeframeResponse(BaseModel):
    competition_id: int
    competition_name: str
    upload_start: datetime
    upload_end: datetime
    evaluation_start: datetime
    evaluation_end: datetime


class SweMinerSummary(BaseModel):
    hotkey: str
    total_score: Optional[float] = None
    screener_passed: Optional[bool] = None
    category_scores: Optional[dict[str, float]] = None
    task_count: int = 0
    screener_task_count: int = 0


class SweMinerTaskResultItem(BaseModel):
    task_id: int
    task_name: str
    is_screener: bool = False
    pass_without_compression: Optional[bool] = None
    pass_with_compression: Optional[bool] = None
    tokens_without_compression: Optional[int] = None
    tokens_with_compression: Optional[float] = None
    input_tokens_with_compression: Optional[float] = None
    cached_input_tokens_with_compression: Optional[float] = None
    output_tokens_with_compression: Optional[float] = None
    platform_score: Optional[float] = None
    run_count: int = 0


class SweMinerTaskRunItem(BaseModel):
    run_id: int
    attempt_no: int
    pass_with_compression: Optional[bool] = None
    tokens_with_compression: Optional[int] = None
    input_tokens_with_compression: Optional[int] = None
    cached_input_tokens_with_compression: Optional[int] = None
    output_tokens_with_compression: Optional[int] = None
    weighted_tokens_with_compression: Optional[float] = None
    platform_score: Optional[float] = None
    time_taken_seconds: Optional[float] = None
    agent_steps: Optional[int] = None


class SweMinerPenaltySummary(BaseModel):
    categories: dict[str, Optional[float]] = Field(default_factory=dict)
    total: Optional[float] = None


class SweMinerTaskAggregateItem(BaseModel):
    task: SweMinerTaskResultItem
    runs: list[SweMinerTaskRunItem] = Field(default_factory=list)
    total_runs: int = 0
    benchmark_type: Optional[str] = None
    baseline_weighted_tokens: Optional[float] = None
    miner_weighted_tokens: Optional[float] = None
    baseline_input_tokens: Optional[int] = None
    baseline_cached_input_tokens: Optional[int] = None
    baseline_output_tokens: Optional[int] = None
    miner_input_tokens: Optional[int] = None
    miner_cached_input_tokens: Optional[int] = None
    miner_output_tokens: Optional[int] = None


class SweCompetitionMinerAggregateItem(BaseModel):
    miner: SweMinerSummary
    status: str
    last_submit: Optional[datetime] = None
    registered_at: Optional[datetime] = None
    contests: int = 0
    rank: Optional[int] = None
    penalties: SweMinerPenaltySummary
    tasks: list[SweMinerTaskAggregateItem] = Field(default_factory=list)
    total_tasks: int = 0
    baseline_weighted_tokens_total: Optional[float] = None
    miner_weighted_tokens_total: Optional[float] = None
    baseline_input_tokens_total: Optional[int] = None
    baseline_cached_input_tokens_total: Optional[int] = None
    baseline_output_tokens_total: Optional[int] = None
    miner_input_tokens_total: Optional[int] = None
    miner_cached_input_tokens_total: Optional[int] = None
    miner_output_tokens_total: Optional[int] = None


class SweCompetitionAggregateResponse(BaseModel):
    competition_id: int
    competition_name: str
    competition_type: Literal["swe"] = "swe"
    timeframe: Optional[CurrentCompetitionTimeframeResponse] = None
    miners: list[SweCompetitionMinerAggregateItem] = Field(default_factory=list)
    total_miners: int = 0
