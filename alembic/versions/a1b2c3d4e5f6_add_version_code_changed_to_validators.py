"""Add version and code_changed to validators.

Revision ID: a1b2c3d4e5f6
Revises: b6e4c2d1f9a8
Create Date: 2026-03-25
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "b6e4c2d1f9a8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("validators"):
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns("validators")
    }

    if "version" not in existing_columns:
        op.add_column(
            "validators",
            sa.Column("version", sa.String(128), nullable=True),
        )

    if "code_changed" not in existing_columns:
        op.add_column(
            "validators",
            sa.Column("code_changed", sa.Boolean(), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("validators"):
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns("validators")
    }

    if "code_changed" in existing_columns:
        op.drop_column("validators", "code_changed")

    if "version" in existing_columns:
        op.drop_column("validators", "version")
