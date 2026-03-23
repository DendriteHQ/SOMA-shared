from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Request(Base):
    __tablename__ = "requests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    external_request_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    payload: Mapped[dict | list] = mapped_column(JSON, nullable=False)
    status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
    db_query_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    db_error_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    db_total_duration_ms: Mapped[float | None] = mapped_column(
        DOUBLE_PRECISION,
        nullable=True,
    )
    db_slow_query_count: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    db_operation_counts: Mapped[dict[str, int] | None] = mapped_column(JSON, nullable=True)
    db_slowest_query_ms: Mapped[float | None] = mapped_column(
        DOUBLE_PRECISION,
        nullable=True,
    )
    db_slowest_query_operation: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    db_slowest_query_preview: Mapped[str | None] = mapped_column(Text, nullable=True)
