from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, JSON, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class BatchQuestionScore(Base):
    __tablename__ = "batch_question_scores"
    __table_args__ = (
        UniqueConstraint(
            "batch_challenge_fk",
            "question_fk",
            "validator_fk",
            name="uq_batch_question_scores_batch_challenge_question_validator",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    batch_challenge_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("batch_challenges.id", ondelete="CASCADE"),
        nullable=False,
    )
    question_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    validator_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("validators.id"),
        nullable=False,
    )
    score: Mapped[float] = mapped_column(
        Numeric(10, 4),
        nullable=False,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
