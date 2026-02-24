from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Miner(Base):
    __tablename__ = "miners"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ss58: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
