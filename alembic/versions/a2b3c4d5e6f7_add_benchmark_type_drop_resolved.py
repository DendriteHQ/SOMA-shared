"""add benchmark_type to swe_bench_runs, drop resolved from swe_bench_run_validations

Revision ID: a2b3c4d5e6f7
Revises: f1e2d3c4b5a6
Create Date: 2026-06-25

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "a2b3c4d5e6f7"
down_revision = "f1e2d3c4b5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "swe_bench_runs",
        sa.Column(
            "benchmark_type",
            sa.String(length=64),
            nullable=False,
            server_default="swebench_verified",
        ),
    )
    op.drop_column("swe_bench_run_validations", "resolved")


def downgrade() -> None:
    op.add_column(
        "swe_bench_run_validations",
        sa.Column("resolved", sa.Boolean(), nullable=True),
    )
    op.drop_column("swe_bench_runs", "benchmark_type")
