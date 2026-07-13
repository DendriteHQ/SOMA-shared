"""add compression_logs_uuid to swe bench runs

Revision ID: a4d6f8b2c0e3
Revises: e9c1a3b5d7f2
Create Date: 2026-07-10

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "a4d6f8b2c0e3"
down_revision = "e9c1a3b5d7f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "swe_bench_runs",
        sa.Column("compression_logs_uuid", sa.Text(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_swe_bench_runs_compression_logs_uuid",
        "swe_bench_runs",
        ["compression_logs_uuid"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_swe_bench_runs_compression_logs_uuid",
        "swe_bench_runs",
        type_="unique",
    )
    op.drop_column("swe_bench_runs", "compression_logs_uuid")
