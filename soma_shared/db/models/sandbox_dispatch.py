from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


DISPATCH_OUTCOMES = ("accepted", "rejected", "error", "ack_timeout")
CLOSED_REASONS = ("reported", "ttl_expired")


class SandboxDispatch(Base):
    """One attempt to hand a SWE-bench run to a sandbox, and how it ended.

    A journal of sandbox work, not part of the run's state: rows outlive the run
    (``run_id`` deliberately has no foreign key, because the auto-run-restarter deletes
    failed runs) so per-sandbox throughput and errors stay countable. Every URL tried
    for a run, including fallbacks, is its own row with its own ``dispatch_id``.
    Capacity rejections (HTTP 429) are not journaled.
    """

    __tablename__ = "sandbox_dispatches"
    __table_args__ = (
        CheckConstraint(
            "dispatch_outcome IN ('accepted', 'rejected', 'error', 'ack_timeout')",
            name="ck_sandbox_dispatches_dispatch_outcome",
        ),
        CheckConstraint(
            "closed_reason IS NULL OR closed_reason IN ('reported', 'ttl_expired')",
            name="ck_sandbox_dispatches_closed_reason",
        ),
        Index("ix_sandbox_dispatches_sandbox_id_dispatched_at", "sandbox_id", "dispatched_at"),
        Index("ix_sandbox_dispatches_sandbox_url_dispatched_at", "sandbox_url", "dispatched_at"),
        Index("ix_sandbox_dispatches_run_id", "run_id"),
        Index("ix_sandbox_dispatches_competition_fk_instance_id", "competition_fk", "instance_id"),
        Index("ix_sandbox_dispatches_dispatched_at", "dispatched_at"),
    )

    # Assigned by the run coordinator and echoed by the sandbox in its acknowledgement
    # and result callback.
    dispatch_id: Mapped[str] = mapped_column(Text, primary_key=True)
    run_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Where the attempt went: the configured URL (NULL for a row created from a result
    # callback whose dispatch the coordinator never journaled), and the identity the
    # sandbox host reported for itself (NULL when it answered nothing or has none set).
    sandbox_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    sandbox_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    # 1-based position among the sandboxes tried for this run in one dispatch pass.
    attempt_index: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    # Copied from the run and its task for filtering; no foreign keys, so they survive
    # deletions. ``instance_id`` is the task's benchmark instance (swe_bench_tasks), kept
    # as text because tasks are deleted along with their competition.
    competition_fk: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    instance_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    miner_fk: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    benchmark_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    baseline_run: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    dispatched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    # accepted | rejected | error | ack_timeout. An ack_timeout may still have been
    # accepted by the sandbox; its result callback then fills in the report columns.
    dispatch_outcome: Mapped[str] = mapped_column(String(32), nullable=False)
    dispatch_http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dispatch_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Filled from the sandbox's result callback.
    reported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    report_ok: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_class: Mapped[str | None] = mapped_column(String(64), nullable=True)
    execution_time_seconds: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    agent_steps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tokens_used: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Whether the callback changed the run. False when the run was already final or
    # no longer exists (e.g. deleted by the auto-run-restarter).
    report_applied: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # reported | ttl_expired; NULL while the attempt is still open.
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_reason: Mapped[str | None] = mapped_column(String(32), nullable=True)
