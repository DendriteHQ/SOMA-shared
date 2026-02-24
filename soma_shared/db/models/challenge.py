from __future__ import annotations

from sqlalchemy import BigInteger, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    challenge_text: Mapped[str] = mapped_column(Text, nullable=False)
    challenge_name: Mapped[str] = mapped_column(Text, nullable=False)
    generation_timestamp: Mapped[str] = mapped_column(Text, nullable=False)
