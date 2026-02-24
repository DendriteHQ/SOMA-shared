from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ValidatorHeartbeat(Base):
    __tablename__ = "validator_heartbeats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    validator_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("validators.id"),
        nullable=False,
    )
    request_fk: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("requests.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
