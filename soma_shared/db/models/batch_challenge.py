from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Index, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class BatchChallenge(Base):
    __tablename__ = "batch_challenges"
    __table_args__ = (
        UniqueConstraint(
            "challenge_batch_fk",
            "challenge_fk",
            "compression_ratio",
            name="uq_batch_challenges_batch_challenge",
        ),
        Index(
            "ix_batch_challenges_challenge_fk_challenge_batch_fk",
            "challenge_fk",
            "challenge_batch_fk",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    challenge_batch_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("challenge_batches.id", ondelete="CASCADE"),
        nullable=False,
    )
    challenge_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("challenges.id", ondelete="RESTRICT"),
        nullable=False,
    )
    compression_ratio: Mapped[float] = mapped_column(
        Numeric(10, 4),
        nullable=False,
    )
