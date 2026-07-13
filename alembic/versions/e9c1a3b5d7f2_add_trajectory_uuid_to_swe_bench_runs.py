"""add trajectory_uuid to swe bench runs

Revision ID: e9c1a3b5d7f2
Revises: a2b3c4d5e6f7, b3f1d8a7c2e4
Create Date: 2026-07-10

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "e9c1a3b5d7f2"
down_revision = ("a2b3c4d5e6f7", "b3f1d8a7c2e4")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "swe_bench_runs",
        sa.Column("trajectory_uuid", sa.Text(), nullable=True),
    )
    op.create_unique_constraint(
        "uq_swe_bench_runs_trajectory_uuid",
        "swe_bench_runs",
        ["trajectory_uuid"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_swe_bench_runs_trajectory_uuid",
        "swe_bench_runs",
        type_="unique",
    )
    op.drop_column("swe_bench_runs", "trajectory_uuid")
