"""Drop unused request metric columns.

Revision ID: 4a1b2c3d4e5f
Revises: 0c7e4b1d2f9a
Create Date: 2026-03-23
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "4a1b2c3d4e5f"
down_revision = "0c7e4b1d2f9a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    existing_columns = {column["name"] for column in inspector.get_columns("requests")}
    for column_name in (
        "db_max_duration_ms",
        "db_pool_checkin_count",
        "db_pool_checkout_count",
        "db_pool_connect_count",
    ):
        if column_name in existing_columns:
            op.drop_column("requests", column_name)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    existing_columns = {column["name"] for column in inspector.get_columns("requests")}
    new_columns = (
        sa.Column("db_max_duration_ms", sa.Double(), nullable=True),
        sa.Column("db_pool_connect_count", sa.BigInteger(), nullable=True),
        sa.Column("db_pool_checkout_count", sa.BigInteger(), nullable=True),
        sa.Column("db_pool_checkin_count", sa.BigInteger(), nullable=True),
    )
    for column in new_columns:
        if column.name not in existing_columns:
            op.add_column("requests", column)