from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ScreeningChallenge(Base):
    __tablename__ = "screening_challenges"
    __table_args__ = (
        Index(
            "ix_screening_challenges_screener_fk_challenge_fk",
            "screener_fk",
            "challenge_fk",
        ),
        Index(
            "ix_screening_challenges_challenge_fk_screener_fk",
            "challenge_fk",
            "screener_fk",
        ),
    )

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
