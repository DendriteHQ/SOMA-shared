from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar, Literal, List
from pydantic import BaseModel, Field, field_validator
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

class PostChallengeScores(BaseModel):
    batch_id: str
    question_scores: list[QuestionScore]
    
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
