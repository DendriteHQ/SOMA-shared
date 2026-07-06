from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class SweExplorerValidation(Base):
    __tablename__ = "swe_explorer_validations"

    validation_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("swe_bench_run_validations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    precision: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    recall: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    f1_score: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    hit_file_rate: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    noise_file_rate: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    weighted_core_coverage: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
