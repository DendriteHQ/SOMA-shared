from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CompetitionConfig(Base):
    __tablename__ = "competition_configs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    competition_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("competitions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
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
