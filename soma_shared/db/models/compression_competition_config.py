from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CompressionCompetitionConfig(Base):
    __tablename__ = "compression_competition_config"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    competition_config_fk: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("competition_configs.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    compression_ratios: Mapped[list[float]] = mapped_column(
        JSON,
        nullable=False,
    )
    is_partial_winner: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
