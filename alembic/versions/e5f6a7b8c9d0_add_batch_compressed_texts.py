"""Add batch_compressed_texts table.

Revision ID: e5f6a7b8c9d0
Revises: 8d4a6a71f2b1
Create Date: 2026-03-07
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "e5f6a7b8c9d0"
down_revision = "8d4a6a71f2b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("batch_compressed_texts"):
        return

    op.create_table(
        "batch_compressed_texts",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("batch_challenge_fk", sa.BigInteger(), nullable=False),
        sa.Column("storage_uuid", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["batch_challenge_fk"],
            ["batch_challenges.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "batch_challenge_fk",
            name="uq_batch_compressed_texts_batch_challenge",
        ),
        sa.UniqueConstraint("storage_uuid"),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("batch_compressed_texts"):
        return

    op.drop_table("batch_compressed_texts")
