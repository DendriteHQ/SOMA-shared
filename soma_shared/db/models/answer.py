from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    question_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
    )
    answer: Mapped[str] = mapped_column(Text, nullable=False)
