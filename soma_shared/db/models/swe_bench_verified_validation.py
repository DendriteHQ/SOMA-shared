from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class SweBenchVerifiedValidation(Base):
    __tablename__ = "swe_bench_verified_validations"

    validation_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("swe_bench_run_validations.id", ondelete="CASCADE"),
        primary_key=True,
    )
    resolved: Mapped[bool] = mapped_column(Boolean, nullable=False)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
