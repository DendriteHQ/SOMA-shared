"""Add database metrics columns to requests.

Revision ID: 0c7e4b1d2f9a
Revises: e5f6a7b8c9d0, f1c9a7b4d2e3
Create Date: 2026-03-20
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "0c7e4b1d2f9a"
down_revision = ("e5f6a7b8c9d0", "f1c9a7b4d2e3")
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    if inspector.has_table("db_slow_query_events"):
        existing_indexes = {index["name"] for index in inspector.get_indexes("db_slow_query_events")}
        for index_name in (
            "ix_db_slow_query_events_operation",
            "ix_db_slow_query_events_instance_id",
            "ix_db_slow_query_events_app_name",
            "ix_db_slow_query_events_created_at",
        ):
            if index_name in existing_indexes:
                op.drop_index(index_name, table_name="db_slow_query_events")
        op.drop_table("db_slow_query_events")

    if inspector.has_table("db_query_metrics_minute"):
        existing_indexes = {index["name"] for index in inspector.get_indexes("db_query_metrics_minute")}
        for index_name in (
            "ix_db_query_metrics_minute_instance_id",
            "ix_db_query_metrics_minute_app_name",
            "ix_db_query_metrics_minute_bucket_ts",
        ):
            if index_name in existing_indexes:
                op.drop_index(index_name, table_name="db_query_metrics_minute")
        op.drop_table("db_query_metrics_minute")

    existing_columns = {column["name"] for column in inspector.get_columns("requests")}
    new_columns = (
        sa.Column("db_query_count", sa.BigInteger(), nullable=True),
        sa.Column("db_error_count", sa.BigInteger(), nullable=True),
        sa.Column("db_total_duration_ms", sa.Double(), nullable=True),
        sa.Column("db_max_duration_ms", sa.Double(), nullable=True),
        sa.Column("db_slow_query_count", sa.BigInteger(), nullable=True),
        sa.Column("db_pool_connect_count", sa.BigInteger(), nullable=True),
        sa.Column("db_pool_checkout_count", sa.BigInteger(), nullable=True),
        sa.Column("db_pool_checkin_count", sa.BigInteger(), nullable=True),
        sa.Column("db_operation_counts", sa.JSON(), nullable=True),
        sa.Column("db_slowest_query_ms", sa.Double(), nullable=True),
        sa.Column("db_slowest_query_operation", sa.String(length=50), nullable=True),
        sa.Column("db_slowest_query_preview", sa.Text(), nullable=True),
    )
    for column in new_columns:
        if column.name not in existing_columns:
            op.add_column("requests", column)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)

    existing_columns = {column["name"] for column in inspector.get_columns("requests")}
    for column_name in (
        "db_slowest_query_preview",
        "db_slowest_query_operation",
        "db_slowest_query_ms",
        "db_operation_counts",
        "db_pool_checkin_count",
        "db_pool_checkout_count",
        "db_pool_connect_count",
        "db_slow_query_count",
        "db_max_duration_ms",
        "db_total_duration_ms",
        "db_error_count",
        "db_query_count",
    ):
        if column_name in existing_columns:
            op.drop_column("requests", column_name)