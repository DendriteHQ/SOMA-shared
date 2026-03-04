"""Add miner_banned_status to miners.

Revision ID: 8d4a6a71f2b1
Revises: 6f3f1e2d9a7b
Create Date: 2026-03-04
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "8d4a6a71f2b1"
down_revision = "6f3f1e2d9a7b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("miners"):
        return

    miner_columns = {column["name"] for column in inspector.get_columns("miners")}
    if "miner_banned_status" in miner_columns:
        return

    op.add_column(
        "miners",
        sa.Column(
            "miner_banned_status",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("miners"):
        return

    miner_columns = {column["name"] for column in inspector.get_columns("miners")}
    if "miner_banned_status" not in miner_columns:
        return

    op.drop_column("miners", "miner_banned_status")
