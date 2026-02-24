from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class BatchQuestionAnswer(Base):
    __tablename__ = "batch_question_answers"
    __table_args__ = (
        UniqueConstraint(
            "batch_challenge_fk",
            "question_fk",
            name="uq_batch_question_answers_batch_challenge_question",
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
    produced_answer: Mapped[str] = mapped_column(Text, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
