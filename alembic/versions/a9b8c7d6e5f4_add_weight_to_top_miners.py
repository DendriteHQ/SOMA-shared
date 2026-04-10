"""Add weight column to top_miners table.

Revision ID: a9b8c7d6e5f4
Revises: c1a2b3d4e5f6
Create Date: 2026-04-09

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "a9b8c7d6e5f4"
down_revision = "c1a2b3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "top_miners",
        sa.Column(
            "weight",
            sa.Float(),
            nullable=False,
            server_default="0.0",
        ),
    )
    # Set existing rows to 0.0 explicitly
    op.execute(sa.text("UPDATE top_miners SET weight = 0.0 WHERE weight IS NULL"))


def downgrade() -> None:
    op.drop_column("top_miners", "weight")
