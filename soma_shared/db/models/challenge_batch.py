from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ChallengeBatch(Base):
    __tablename__ = "challenge_batches"
    __table_args__ = (
        Index("ix_challenge_batches_script_fk", "script_fk"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    miner_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("miners.id"),
        nullable=False,
    )
    script_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("scripts.id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
