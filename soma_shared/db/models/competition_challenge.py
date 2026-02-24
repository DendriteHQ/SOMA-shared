from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CompetitionChallenge(Base):
    __tablename__ = "competition_challenges"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    competition_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("competitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    challenge_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("challenges.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
