from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class TerminalBenchValidation(Base):
    __tablename__ = "terminal_bench_validations"

    validation_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("swe_bench_run_validations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    score: Mapped[bool] = mapped_column(Boolean, nullable=False)
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
