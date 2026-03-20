from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Validator(Base):
    __tablename__ = "validators"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ss58: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    port: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    current_status: Mapped[str] = mapped_column(String(32), nullable=False)
    is_archive: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
