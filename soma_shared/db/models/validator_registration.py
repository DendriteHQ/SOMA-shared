from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class ValidatorRegistration(Base):
    __tablename__ = "validator_registrations"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    validator_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("validators.id"),
        nullable=False,
    )
    request_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("requests.id", ondelete="SET NULL"),
        nullable=True,
    )
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    port: Mapped[int | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
