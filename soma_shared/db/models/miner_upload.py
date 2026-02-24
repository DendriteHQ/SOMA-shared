from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class MinerUpload(Base):
    __tablename__ = "miner_uploads"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    script_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("scripts.id"),
        nullable=False,
    )
    request_fk: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("requests.id"),
        nullable=True,
    )
    competition_fk: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("competitions.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
