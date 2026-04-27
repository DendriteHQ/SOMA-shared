from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CompetitionChallenge(Base):
    __tablename__ = "competition_challenges"
    __table_args__ = (
        Index(
            "ix_competition_challenges_active_competition_fk_challenge_fk",
            "competition_fk",
            "challenge_fk",
            postgresql_where=text("is_active = true"),
        ),
        Index(
            "ix_competition_challenges_active_challenge_fk_competition_fk",
            "challenge_fk",
            "competition_fk",
            postgresql_where=text("is_active = true"),
        ),
    )

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
