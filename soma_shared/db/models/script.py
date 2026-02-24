from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Script(Base):
    __tablename__ = "scripts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    script_uuid: Mapped[str] = mapped_column(
        Uuid(as_uuid=False),
        unique=True,
        nullable=False,
    )
    miner_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("miners.id"),
        nullable=False,
    )
    request_fk: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("requests.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
