from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Float, String, CheckConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class TopMiner(Base):
    __tablename__ = "top_miners"
    __table_args__ = (
        CheckConstraint(
            "ends_at > starts_at",
            name="chk_top_miner_positive_window",
        ),
        #TODO add alembic extension for creating exclusion constraint with gist index on tstzrange of starts_at and ends_at to prevent overlapping time windows for the same miner
        #text(
        #    "CONSTRAINT excl_top_miner_no_overlap "
        #    "EXCLUDE USING gist (tstzrange(starts_at, ends_at, '[)') WITH &&)"
        #),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    ss58: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
