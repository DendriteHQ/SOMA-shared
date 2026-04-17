"""Add soma_api_key table.

Revision ID: b2d4f6a8c0e1
Revises: 3d2be0724e0c
Create Date: 2026-04-16

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "b2d4f6a8c0e1"
down_revision = "3d2be0724e0c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "soma_api_key",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("prefix", sa.String(length=16), nullable=False),
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("rate_limit_rpm", sa.Integer(), nullable=True),
        sa.Column("rate_limit_rpd", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("prefix"),
    )


def downgrade() -> None:
    op.drop_table("soma_api_key")
