from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class BurnRequest(Base):
    __tablename__ = "burn_requests"
    __table_args__ = (
        CheckConstraint(
            "burn_ratio >= 0 AND burn_ratio <= 1",
            name="ck_burn_requests_burn_ratio_range",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    request_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("requests.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    burn_ratio: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0,
    )
