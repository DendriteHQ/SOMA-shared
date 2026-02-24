from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    challenge_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("challenges.id", ondelete="CASCADE"),
        nullable=False,
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
