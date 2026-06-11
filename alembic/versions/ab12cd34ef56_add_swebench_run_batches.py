"""add swebench run batches

Revision ID: ab12cd34ef56
Revises: 5b8d7e6a9c1f
Create Date: 2026-06-11

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "ab12cd34ef56"
down_revision = "5b8d7e6a9c1f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "swe_bench_run_batches",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column("miner_fk", sa.BigInteger(), nullable=True),
        sa.Column("script_fk", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["miner_fk"], ["miners.id"]),
        sa.ForeignKeyConstraint(["script_fk"], ["scripts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_swe_bench_run_batches_miner_script",
        "swe_bench_run_batches",
        ["miner_fk", "script_fk"],
    )

    op.add_column(
        "swe_bench_runs",
        sa.Column("batch_fk", sa.BigInteger(), nullable=True),
    )
    op.create_foreign_key(
        "fk_swe_bench_runs_batch_fk",
        "swe_bench_runs",
        "swe_bench_run_batches",
        ["batch_fk"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_swe_bench_runs_batch_fk", "swe_bench_runs", ["batch_fk"])


def downgrade() -> None:
    op.drop_index("ix_swe_bench_runs_batch_fk", table_name="swe_bench_runs")
    op.drop_constraint("fk_swe_bench_runs_batch_fk", "swe_bench_runs", type_="foreignkey")
    op.drop_column("swe_bench_runs", "batch_fk")

    op.drop_index("ix_swe_bench_run_batches_miner_script", table_name="swe_bench_run_batches")
    op.drop_table("swe_bench_run_batches")
