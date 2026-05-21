"""add miner openrouter api keys table

Revision ID: 4c6d8e1f2a3b
Revises: 9d1e2f3a4b5c
Create Date: 2026-05-20

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "4c6d8e1f2a3b"
down_revision = "9d1e2f3a4b5c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "miner_openrouter_api_keys",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("miner_fk", sa.BigInteger(), nullable=False),
        sa.Column(
            "secret_backend",
            sa.String(length=64),
            nullable=False,
            server_default="aws_secrets_manager",
        ),
        sa.Column("secret_ref", sa.String(length=512), nullable=False),
        sa.Column("key_fingerprint", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["miner_fk"], ["miners.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("miner_fk"),
        sa.UniqueConstraint("secret_ref"),
    )


def downgrade() -> None:
    op.drop_table("miner_openrouter_api_keys")
