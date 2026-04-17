from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SomaApiKey(Base):
    """API keys for the SOMA frontend API.

    The raw secret is never persisted; only SHA-256(secret) is stored.
    """

    __tablename__ = "soma_api_key"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # First 8 hex chars of the raw key – lookup index, not secret.
    prefix: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    # SHA-256(secret) as hex string.
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    # Per-key rate limit overrides. NULL -> use global default from config.
    rate_limit_rpm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rate_limit_rpd: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
