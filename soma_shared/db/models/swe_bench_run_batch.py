from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class SweBenchRunBatch(Base):
    __tablename__ = "swe_bench_run_batches"
    __table_args__ = (
        Index("ix_swe_bench_run_batches_miner_script", "miner_fk", "script_fk"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    miner_fk: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("miners.id"),
        nullable=True,
    )
    script_fk: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("scripts.id"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
