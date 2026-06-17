from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class FrontendSummaryResponse(BaseModel):
    server_ts: datetime
    miners: int = 0
    validators: int = 0
    active_validators: int = 0
    competitions: int = 0
    active_competitions: int = 0
    competition_challenges: int = 0
    active_competition_challenges: int = 0
    burn_active: bool
    burn_ratio: float = Field(default=1.0, ge=0, le=1)


class Pagination(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int


class MinerCompetitionItem(BaseModel):
    competition_id: int
    competition_name: str
    competition_type: Literal["compression", "swe"]


class PartialScore(BaseModel):
    compression_ratio: float
    score: float


class MinerListItem(BaseModel):
    hotkey: str
    score: Optional[float] = None
    total_score: Optional[float] = None
    partial_scores: Optional[list[PartialScore]] = None
    last_submit: Optional[datetime] = None
    status: str
    screener_score: Optional[float] = None


class MinersListResponse(BaseModel):
    miners: list[MinerListItem]
    pagination: Pagination


class ContestSummary(BaseModel):
    id: int
    name: str
    date: datetime
    score: Optional[float] = None
    partial_scores: Optional[list[PartialScore]] = None
    rank: Optional[int] = None


class SourceCodeSummary(BaseModel):
    available: bool
    code: Optional[str] = None


class MinerDetail(BaseModel):
    hotkey: str
    registered_at: Optional[datetime] = None
    contests: int
    status: str
    total_score: Optional[float] = None
    partial_scores: Optional[list[PartialScore]] = None


class MinerDetailResponse(BaseModel):
    miner: MinerDetail
    last_contest: Optional[ContestSummary] = None
    source_code: SourceCodeSummary


class MinerContestsResponse(BaseModel):
    contests: list[ContestSummary]
    total: int


class ValidatorListItem(BaseModel):
    id: int
    name: str
    status: str
    is_archive: bool = False
    register_date: datetime


class ValidatorsListResponse(BaseModel):
    validators: list[ValidatorListItem]


class ChallengeItem(BaseModel):
    challenge_id: int
    challenge_name: str
    batch_challenge_id: int
    competition_name: str
    competition_id: int
    compression_ratio: float
    created_at: datetime
    score: Optional[float] = None
    scored_at: Optional[datetime] = None


class MinerChallengesResponse(BaseModel):
    challenges: list[ChallengeItem]
    total: int


class QuestionDetail(BaseModel):
    question_id: int
    question_text: str
    miner_answer: Optional[str] = None
    ground_truth_answer: Optional[str] = None
    score: Optional[float] = None
    score_details: Optional[dict] = None


class ChallengeDetail(BaseModel):
    batch_challenge_id: int
    challenge_id: int
    challenge_name: str
    challenge_text: str
    competition_name: str
    competition_id: int
    compression_ratio: float
    created_at: datetime
    overall_score: Optional[float] = None
    questions: list[QuestionDetail]


class ChallengeDetailResponse(BaseModel):
    challenge: ChallengeDetail


class ScreenerChallengesResponse(BaseModel):
    avg_score: Optional[float] = None
    rank: Optional[int] = None
    total_miners: int = 0
    challenges: list[ChallengeDetail]
    total: int


class CurrentCompetitionTimeframeResponse(BaseModel):
    competition_id: int
    competition_name: str
    upload_start: datetime
    upload_end: datetime
    evaluation_start: datetime
    evaluation_end: datetime


class SweMinerLeaderboardItem(BaseModel):
    hotkey: str
    total_score: Optional[float] = None
    screener_passed: Optional[bool] = None
    category_scores: Optional[dict[str, float]] = None


class SweMinersListResponse(BaseModel):
    miners: list[SweMinerLeaderboardItem]
    pagination: Pagination


class SweMinerSummary(BaseModel):
    hotkey: str
    total_score: Optional[float] = None
    screener_passed: Optional[bool] = None
    category_scores: Optional[dict[str, float]] = None
    task_count: int = 0
    screener_task_count: int = 0


class SweMinerSummaryResponse(BaseModel):
    miner: SweMinerSummary


class SweMinerTaskResultItem(BaseModel):
    task_id: int
    task_name: str
    is_screener: bool = False
    pass_without_compression: Optional[bool] = None
    pass_with_compression: Optional[bool] = None
    tokens_without_compression: Optional[int] = None
    tokens_with_compression: Optional[float] = None
    platform_score: Optional[float] = None
    run_count: int = 0


class SweMinerTaskResultsResponse(BaseModel):
    tasks: list[SweMinerTaskResultItem]
    total: int


class SweMinerTaskDetailResponse(BaseModel):
    task: SweMinerTaskResultItem


class SweMinerTaskRunItem(BaseModel):
    run_id: int
    attempt_no: int
    pass_with_compression: Optional[bool] = None
    tokens_with_compression: Optional[int] = None
    platform_score: Optional[float] = None
    time_taken_seconds: Optional[float] = None
    agent_steps: Optional[int] = None


class SweMinerTaskRunsResponse(BaseModel):
    task_id: int
    task_name: str
    is_screener: bool = False
    pass_without_compression: Optional[bool] = None
    tokens_without_compression: Optional[int] = None
    runs: list[SweMinerTaskRunItem]
    total: int


class SweMinerPenaltySummary(BaseModel):
    categories: dict[str, Optional[float]] = Field(default_factory=dict)
    total: Optional[float] = None


class SweMinerTaskAggregateItem(BaseModel):
    task: SweMinerTaskResultItem
    runs: list[SweMinerTaskRunItem] = Field(default_factory=list)
    total_runs: int = 0


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


class SweCompetitionAggregateResponse(BaseModel):
    competition_id: int
    competition_name: str
    competition_type: Literal["swe"] = "swe"
    timeframe: Optional[CurrentCompetitionTimeframeResponse] = None
    miners: list[SweCompetitionMinerAggregateItem] = Field(default_factory=list)
    total_miners: int = 0
