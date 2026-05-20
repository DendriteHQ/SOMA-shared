from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MinerOpenRouterApiKey(Base):
    """Secure key metadata for miner OpenRouter credentials.

    Raw API keys are never stored in Postgres. Only a secret reference
    (for example AWS Secrets Manager ARN/path) and a non-reversible
    fingerprint are persisted.
    """

    __tablename__ = "miner_openrouter_api_keys"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    miner_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("miners.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    secret_backend: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="aws_secrets_manager",
        server_default="aws_secrets_manager",
    )
    secret_ref: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    key_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_utcnow,
        onupdate=_utcnow,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
