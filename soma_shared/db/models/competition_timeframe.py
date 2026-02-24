from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CompetitionTimeframe(Base):
    __tablename__ = "competition_timeframes"
    __table_args__ = (
        CheckConstraint(
            "upload_ends_at > upload_starts_at",
            name="chk_upload_positive_duration",
        ),
        CheckConstraint(
            "eval_ends_at > eval_starts_at",
            name="chk_eval_positive_duration",
        ),
        CheckConstraint(
            "eval_starts_at >= upload_ends_at",
            name="chk_eval_after_upload",
        ),
    )
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    competition_config_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("competition_configs.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    upload_starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    upload_ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    eval_starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    eval_ends_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
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
