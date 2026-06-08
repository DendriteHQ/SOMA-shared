"""Add approved column to top_miners.

Revision ID: c7d8e9f0a1b2
Revises: 5b8d7e6a9c1f
Create Date: 2026-06-08

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "c7d8e9f0a1b2"
down_revision = "5b8d7e6a9c1f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "top_miners",
        sa.Column(
            "approved",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_index(
        "ix_top_miners_approved",
        "top_miners",
        ["approved"],
    )


def downgrade() -> None:
    op.drop_index("ix_top_miners_approved", table_name="top_miners")
    op.drop_column("top_miners", "approved")
