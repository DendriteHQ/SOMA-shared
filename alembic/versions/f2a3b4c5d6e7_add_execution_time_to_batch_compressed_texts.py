"""Add execution_time_seconds to batch_compressed_texts.

Revision ID: f2a3b4c5d6e7
Revises: f1c9a7b4d2e3
Create Date: 2026-03-31
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "f2a3b4c5d6e7"
down_revision = 'e3f4a5b6c7d8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add execution_time_seconds column to batch_compressed_texts table."""
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("batch_compressed_texts"):
        return

    columns = [col["name"] for col in inspector.get_columns("batch_compressed_texts")]
    
    if "execution_time_seconds" not in columns:
        op.add_column(
            "batch_compressed_texts",
            sa.Column(
                "execution_time_seconds",
                sa.Numeric(10, 4),
                nullable=True,
                comment="Time in seconds taken to compress this text in the sandbox",
            ),
        )


def downgrade() -> None:
    """Remove execution_time_seconds column from batch_compressed_texts table."""
    bind = op.get_bind()
    inspector = inspect(bind)

    if not inspector.has_table("batch_compressed_texts"):
        return

    columns = [col["name"] for col in inspector.get_columns("batch_compressed_texts")]
    
    if "execution_time_seconds" in columns:
        op.drop_column("batch_compressed_texts", "execution_time_seconds")
