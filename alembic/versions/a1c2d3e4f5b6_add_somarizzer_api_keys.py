"""Add somarizzer_api_keys table.

Revision ID: a1c2d3e4f5b6
Revises: b1c2d3e4f5a6
Create Date: 2026-04-13

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "a1c2d3e4f5b6"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "somarizzer_api_keys",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("prefix", sa.String(16), nullable=False),
        sa.Column("key_hash", sa.String(64), nullable=False),
        sa.Column("rate_limit_rpm", sa.Integer(), nullable=True),
        sa.Column("rate_limit_rpd", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_miner", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("hotkey", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("prefix"),
    )
    op.create_index(
        "uq_somarizzer_api_keys_active_hotkey",
        "somarizzer_api_keys",
        ["hotkey"],
        unique=True,
        postgresql_where=sa.text("is_active = true AND hotkey IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_somarizzer_api_keys_active_hotkey",
        table_name="somarizzer_api_keys",
    )
    op.drop_table("somarizzer_api_keys")
