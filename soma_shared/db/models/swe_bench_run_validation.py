from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class SweBenchRunValidation(Base):
    __tablename__ = "swe_bench_run_validations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    run_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("swe_bench_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    request_fk: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("requests.id", ondelete="SET NULL"),
        nullable=True,
    )
    validator_fk: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("validators.id"),
        nullable=True,
    )
    logs: Mapped[str | None] = mapped_column(Text, nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    claim_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    scored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
