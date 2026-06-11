from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class SweBenchRun(Base):
    __tablename__ = "swe_bench_runs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    task_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("swe_bench_tasks.id", ondelete="CASCADE"),
        nullable=False,
    )
    request_fk: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("requests.id", ondelete="SET NULL"),
        nullable=True,
    )
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False)
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
    batch_fk: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("swe_bench_run_batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    diff_storage_uuid: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    tokens_used: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    time_taken_seconds: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    agent_steps: Mapped[int | None] = mapped_column(Integer, nullable=True)
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
    baseline_run: Mapped[bool] = mapped_column(Boolean, nullable=False)
