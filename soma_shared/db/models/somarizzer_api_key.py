from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SomarizzerApiKey(Base):
    """API keys for the SOMArizzer service.

    The raw secret is never persisted – only its HMAC-SHA256 hash.
    The prefix (first 8 hex chars) is used as a fast lookup index.

    Key formats:
        Regular:  soma_<prefix>.<secret>
        Miner:    soma_miner_<prefix>.<secret>
    """

    __tablename__ = "somarizzer_api_keys"
    __table_args__ = (
        # Only one active key per hotkey at a time.
        Index(
            "uq_somarizzer_api_keys_active_hotkey",
            "hotkey",
            unique=True,
            postgresql_where=text("is_active = true AND hotkey IS NOT NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    # First 8 hex chars of the raw key – lookup index, not secret.
    prefix: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    # HMAC-SHA256(secret, SALT) as hex string.
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    # Per-key rate limit overrides. NULL → use global default from config.
    rate_limit_rpm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rate_limit_rpd: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    # Miner keys require metagraph membership check on each request.
    is_miner: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    # ss58 hotkey address – only populated for miner keys.
    hotkey: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
