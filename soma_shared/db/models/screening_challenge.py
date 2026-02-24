from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ScreeningChallenge(Base):
    __tablename__ = "screening_challenges"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    screener_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("screeners.id", ondelete="CASCADE"),
        nullable=False,
    )
    challenge_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("challenges.id", ondelete="CASCADE"),
        nullable=False,
    )
