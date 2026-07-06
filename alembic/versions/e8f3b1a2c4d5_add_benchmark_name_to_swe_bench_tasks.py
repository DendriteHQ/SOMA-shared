"""add benchmark name to swe bench tasks

Revision ID: e8f3b1a2c4d5
Revises: c7d8e9f0a1b2
Create Date: 2026-06-18

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "e8f3b1a2c4d5"
down_revision = "c7d8e9f0a1b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "swe_bench_tasks",
        sa.Column("benchmark_name", sa.String(length=128), nullable=True),
    )

    op.execute(
        sa.text(
            """
            UPDATE swe_bench_tasks
            SET benchmark_name = 'SWE-bench/SWE-bench_Verified'
            WHERE benchmark_name IS NULL
            """
        )
    )

    op.alter_column(
        "swe_bench_tasks",
        "benchmark_name",
        existing_type=sa.String(length=128),
        nullable=False,
    )

    op.create_index(
        "ix_swe_bench_tasks_competition_benchmark_instance",
        "swe_bench_tasks",
        ["competition_fk", "benchmark_name", "instance_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_swe_bench_tasks_competition_benchmark_instance",
        table_name="swe_bench_tasks",
    )
    op.drop_column("swe_bench_tasks", "benchmark_name")
