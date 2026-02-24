from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class SignedRequest(Base):
    __tablename__ = "signed_requests"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    request_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("requests.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    nonce: Mapped[str] = mapped_column(Text, nullable=False)
    signer_validator_fk: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("validators.id"),
        nullable=True,
    )
    signer_miner_fk: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("miners.id"),
        nullable=True,
    )
    signer_ss58: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
