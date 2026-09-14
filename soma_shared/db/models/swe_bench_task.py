from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class SweBenchTask(Base):
    __tablename__ = "swe_bench_tasks"
    __table_args__ = (
        CheckConstraint(
            "complexity IN ('short', 'medium', 'long')",
            name="ck_swe_bench_tasks_complexity",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    competition_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("competitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    instance_id: Mapped[str] = mapped_column(String(255), nullable=False)
    benchmark_name: Mapped[str] = mapped_column(String(128), nullable=False)
    planned_repeats: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
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
    is_screener: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    # Screening tier for two-stage screening. NULL = full-evaluation task,
    # 1 = stage-1 liveness/non-regression screener (public, no saving threshold),
    # 2 = stage-2 qualification screener (hidden, saving threshold + ranking).
    # Kept orthogonal to is_screener so existing screener views/frontend that key
    # off is_screener keep working; screener_stage only gates orchestrator seeding,
    # dispatch priority and score inclusion.
    screener_stage: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        default=None,
    )
    # Expected agent effort, set when the task is imported: 'short', 'medium' or
    # 'long'. It is the dimension the incentive layers are built over - winners are
    # picked per complexity subset - so it deliberately does not affect a miner's
    # own score, only which elements that miner competes in.
    #
    # NULL means not classified, and is not backfilled: assigning a category a task
    # was never validated for would enter it into an element it does not belong to.
    # Such a task still counts towards the miner's total score.
    complexity: Mapped[str | None] = mapped_column(
        String(16),
        nullable=True,
        default=None,
    )
