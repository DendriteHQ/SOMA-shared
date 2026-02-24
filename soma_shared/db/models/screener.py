from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Screener(Base):
    __tablename__ = "screeners"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    competition_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("competitions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    screener_name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        onupdate=lambda: datetime.now(timezone.utc),
    )
