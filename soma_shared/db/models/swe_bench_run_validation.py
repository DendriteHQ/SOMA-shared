from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey
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
    validator_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("validators.id"),
        nullable=False,
    )
    resolved: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    scored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
