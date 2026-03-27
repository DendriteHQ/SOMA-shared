from __future__ import annotations

from datetime import datetime
from typing import Optional

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


class MinerListItem(BaseModel):
    hotkey: str
    score: Optional[float] = None
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
