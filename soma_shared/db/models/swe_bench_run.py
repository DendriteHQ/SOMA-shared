from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
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
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    diff_storage_uuid: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    trajectory_uuid: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    compression_logs_uuid: Mapped[str | None] = mapped_column(Text, nullable=True, unique=True)
    tokens_used: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    cached_input_tokens: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Compressor services the run's compressor called through the proxy (Jev, the
    # TypeSafe decision model). Kept apart from the agent's LLM tokens above, which
    # they are never part of: tokens_used stays the agent's total. Jev bills input
    # only. NULL means the run reported no service usage (e.g. a baseline run).
    jev_calls: Mapped[int | None] = mapped_column(Integer, nullable=True)
    jev_input_tokens: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    jev_cost_usd: Mapped[float | None] = mapped_column(Numeric(14, 8), nullable=True)
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
    benchmark_type: Mapped[str] = mapped_column(String(64), nullable=False, server_default="swebench_verified")
