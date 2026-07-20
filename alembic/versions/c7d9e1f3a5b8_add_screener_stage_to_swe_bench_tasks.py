"""add screener_stage to swe_bench_tasks

Revision ID: c7d9e1f3a5b8
Revises: e9c1a3b5d7f2
Create Date: 2026-07-16

Introduces the two-stage screening tier column on swe_bench_tasks:
    NULL = full-evaluation task
    1    = stage-1 liveness / non-regression screener (public, no saving threshold)
    2    = stage-2 qualification screener (hidden, saving threshold + ranking)

Backfill: existing screener tasks (is_screener = TRUE) become stage 2, since
today's single screener is the qualification gate that feeds top-N selection.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "c7d9e1f3a5b8"
down_revision = "e9c1a3b5d7f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "swe_bench_tasks",
        sa.Column("screener_stage", sa.Integer(), nullable=True),
    )
    # Existing screeners become the stage-2 qualification tier.
    op.execute(
        sa.text(
            "UPDATE swe_bench_tasks SET screener_stage = 2 WHERE is_screener = TRUE"
        )
    )
    # Partial index: dispatch/seeding filters on screener_stage constantly and
    # only a small fraction of tasks are screeners.
    op.create_index(
        "ix_swe_bench_tasks_screener_stage",
        "swe_bench_tasks",
        ["competition_fk", "screener_stage"],
        postgresql_where=sa.text("screener_stage IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_swe_bench_tasks_screener_stage",
        table_name="swe_bench_tasks",
    )
    op.drop_column("swe_bench_tasks", "screener_stage")
