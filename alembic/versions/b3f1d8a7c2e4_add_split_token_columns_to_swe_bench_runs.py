"""add split token columns to swe bench runs

Revision ID: b3f1d8a7c2e4
Revises: 5b8d7e6a9c1f
Create Date: 2026-06-18

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "b3f1d8a7c2e4"
down_revision = "5b8d7e6a9c1f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "swe_bench_runs",
        sa.Column("input_tokens", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "swe_bench_runs",
        sa.Column("cached_input_tokens", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "swe_bench_runs",
        sa.Column("output_tokens", sa.BigInteger(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("swe_bench_runs", "output_tokens")
    op.drop_column("swe_bench_runs", "cached_input_tokens")
    op.drop_column("swe_bench_runs", "input_tokens")
