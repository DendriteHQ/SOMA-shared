from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class SweExplorerValidation(Base):
    __tablename__ = "swe_explorer_validations"

    validation_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("swe_bench_run_validations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    primary_metric: Mapped[str] = mapped_column(String(64), nullable=False)
    precision: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    recall: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    f1_score: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    hit_file_rate: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    noise_file_rate: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    hit_region_rate: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    noise_region_rate: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    weighted_core_coverage: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    context_efficiency: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    optional_coverage: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    ndcg_at_100: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    ndcg_at_300: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    ndcg_at_500: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    recall_at_100: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    recall_at_300: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    recall_at_500: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    first_useful_hit: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
