"""Add model to validators.

Revision ID: b7c8d9e0f1a2
Revises: a1b2c3d4e5f6
Create Date: 2026-03-27
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "b7c8d9e0f1a2"
down_revision = "a1b2c3d4e5f6"
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

    if "model" not in existing_columns:
        op.add_column(
            "validators",
            sa.Column("model", sa.String(256), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("validators"):
        return

    existing_columns = {
        column["name"] for column in inspector.get_columns("validators")
    }

    if "model" in existing_columns:
        op.drop_column("validators", "model")
