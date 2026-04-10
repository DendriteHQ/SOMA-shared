"""Add response_payload column to requests table.

Revision ID: b1c2d3e4f5a6
Revises: 4a1b2c3d4e5f
Create Date: 2026-04-10
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision = "b1c2d3e4f5a6"
down_revision = "a9b8c7d6e5f4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("requests")}
    if "response_payload" not in existing_columns:
        op.add_column(
            "requests",
            sa.Column("response_payload", JSONB, nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("requests")}
    if "response_payload" in existing_columns:
        op.drop_column("requests", "response_payload")
