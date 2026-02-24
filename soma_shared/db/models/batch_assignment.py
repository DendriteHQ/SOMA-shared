from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class BatchAssignment(Base):
    __tablename__ = "batch_assignments"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    challenge_batch_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("challenge_batches.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    validator_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("validators.id"),
        nullable=False,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    done_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
