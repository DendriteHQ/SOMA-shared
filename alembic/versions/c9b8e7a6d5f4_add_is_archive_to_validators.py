"""Add is_archive to validators.

Revision ID: c9b8e7a6d5f4
Revises: e5f6a7b8c9d0, f1c9a7b4d2e3
Create Date: 2026-03-18
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "c9b8e7a6d5f4"
down_revision = ("e5f6a7b8c9d0", "f1c9a7b4d2e3")
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("validators"):
        return

    validator_columns = {
        column["name"] for column in inspector.get_columns("validators")
    }
    if "is_archive" in validator_columns:
        return

    op.add_column(
        "validators",
        sa.Column(
            "is_archive",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("validators"):
        return

    validator_columns = {
        column["name"] for column in inspector.get_columns("validators")
    }
    if "is_archive" not in validator_columns:
        return

    op.drop_column("validators", "is_archive")
