from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import TypeVar
from pydantic import BaseModel, Field, field_validator, model_validator
from soma_shared.contracts.common.utils import require_tz

T = TypeVar("T")

class HeartbeatRequest(BaseModel):
    ts: datetime
    version: str

    @field_validator("ts", mode="after")
    @classmethod
    def _validate_timezone(cls, value: datetime, info):
        return require_tz(value, info.field_name)

class HeartbeatResponse(BaseModel):
    ok: bool
    server_ts: datetime
    version: str | None = None
    code_changed: bool | None = None
    model: str | None = None

class ValidatorRegisterRequest(BaseModel):
    validator_hotkey: str
    serving_ip: str
    serving_port: int

class ValidatorRegisterResponse(BaseModel):
    ok: bool

class GetChallengesResponse(BaseModel):
    batch_id: str
    challenges: list[Challenge]

class QuestionScore(BaseModel):
    batch_challenge_id: str
    question_id: str
    produced_answer: str
    score: float
    details: dict | None = None


class ScoreSubmissionType(str, Enum):
    SCORES = "scores"
    ERROR = "error"


class PostChallengeScores(BaseModel):
    batch_id: str
    question_scores: list[QuestionScore] = Field(default_factory=list)
    submission_type: ScoreSubmissionType = ScoreSubmissionType.SCORES
    error_code: str | None = None
    error_message: str | None = None
    error_details: dict | None = None
    retryable: bool = False

    @model_validator(mode="after")
    def _validate_submission(self):
        if self.submission_type == ScoreSubmissionType.SCORES:
            if not self.question_scores:
                raise ValueError(
                    "question_scores must be provided when submission_type='scores'"
                )
            if self.error_code:
                raise ValueError(
                    "error_code must be empty when submission_type='scores'"
                )
            return self

        if self.question_scores:
            raise ValueError(
                "question_scores must be empty when submission_type='error'"
            )
        if not (self.error_code or "").strip():
            raise ValueError(
                "error_code must be provided when submission_type='error'"
            )
        return self
    
class PostChallengeScoresResponse(BaseModel):
    ok: bool
    
class GetChallengesRequest(BaseModel):
    pass
    
class GetBestMinersUidRequest(BaseModel):
    pass

class MinerWeight(BaseModel):
    uid: int
    weight: float

class GetBestMinersUidResponse(BaseModel):
    miners: list[MinerWeight]

class Challenge(BaseModel):
    batch_challenge_id: str
    compressed_text: str
    challenge_questions: list[QA]
    
class QA(BaseModel):
    question_id: str
    question: str
    answer: str
