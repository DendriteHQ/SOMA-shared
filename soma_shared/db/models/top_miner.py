from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Float, String, CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class TopMiner(Base):
    __tablename__ = "top_miners"
    __table_args__ = (
        CheckConstraint(
            "ends_at > starts_at",
            name="chk_top_miner_positive_window",
        ),
        CheckConstraint(
            "winner_type IN ('overall', 'compression_ratio')",
            name="chk_top_miner_winner_type",
        ),
        CheckConstraint(
            "("
            "(winner_type = 'overall' AND compression_ratio IS NULL) "
            "OR "
            "(winner_type = 'compression_ratio' AND compression_ratio IS NOT NULL)"
            ")",
            name="chk_top_miner_category_shape",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ss58: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    competition_fk: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("competitions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    winner_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="overall",
        server_default="overall",
        index=True,
    )
    compression_ratio: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        index=True,
    )
    weight: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=0.0,
        server_default="0.0",
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    miner_fk: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("miners.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    script_fk: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("scripts.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
