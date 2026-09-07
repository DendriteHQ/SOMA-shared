"""add complexity to swe_bench_tasks

Revision ID: b7e2c4a9f0d1
Revises: 4dfe5a976173
Create Date: 2026-09-07

Introduces the task complexity category used to build the incentive layers:
    NULL     = not classified
    'short'  / 'medium' / 'long'

Deliberately nullable with no backfill: guessing a category for an existing task
would put it in a layer element it was never validated for. A task with no
complexity still counts towards a miner's total score - it simply competes in no
complexity layer. The platform falls back to a single, complexity-blind element
while no task in a competition is classified.

The CHECK constraint is what keeps the three values authoritative in the database
rather than only in the importer that writes them.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "b7e2c4a9f0d1"
down_revision = "4dfe5a976173"
branch_labels = None
depends_on = None

_ALLOWED = ("short", "medium", "long")


def upgrade() -> None:
    op.add_column(
        "swe_bench_tasks",
        sa.Column("complexity", sa.String(length=16), nullable=True),
    )
    op.create_check_constraint(
        "ck_swe_bench_tasks_complexity",
        "swe_bench_tasks",
        sa.column("complexity").in_(_ALLOWED),
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_swe_bench_tasks_complexity",
        "swe_bench_tasks",
        type_="check",
    )
    op.drop_column("swe_bench_tasks", "complexity")
