"""add benchmark specific validation tables

Revision ID: f1e2d3c4b5a6
Revises: e8f3b1a2c4d5
Create Date: 2026-06-18

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "f1e2d3c4b5a6"
down_revision = "e8f3b1a2c4d5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "swe_bench_verified_validations",
        sa.Column("validation_fk", sa.BigInteger(), nullable=False),
        sa.Column("score", sa.Boolean(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["validation_fk"],
            ["swe_bench_run_validations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("validation_fk"),
    )

    op.create_table(
        "swe_explorer_validations",
        sa.Column("validation_fk", sa.BigInteger(), nullable=False),
        sa.Column("primary_metric", sa.String(length=64), nullable=False),
        sa.Column("precision", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("recall", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("f1_score", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("hit_file_rate", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("noise_file_rate", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("hit_region_rate", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("noise_region_rate", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("weighted_core_coverage", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("context_efficiency", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("optional_coverage", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("ndcg_at_100", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("ndcg_at_300", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("ndcg_at_500", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("recall_at_100", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("recall_at_300", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("recall_at_500", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("first_useful_hit", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["validation_fk"],
            ["swe_bench_run_validations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("validation_fk"),
    )

    op.create_table(
        "terminal_bench_validations",
        sa.Column("validation_fk", sa.BigInteger(), nullable=False),
        sa.Column("score", sa.Boolean(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["validation_fk"],
            ["swe_bench_run_validations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("validation_fk"),
    )

    # Backfill existing SWE-bench Verified validations from legacy boolean field.
    op.execute(
        sa.text(
            """
            INSERT INTO swe_bench_verified_validations (validation_fk, score, details)
            SELECT
                v.id AS validation_fk,
                COALESCE(v.resolved, FALSE) AS score,
                NULL::json AS details
            FROM swe_bench_run_validations v
            JOIN swe_bench_runs r ON r.id = v.run_fk
            JOIN swe_bench_tasks t ON t.id = r.task_fk
            WHERE t.benchmark_name = 'SWE-bench/SWE-bench_Verified'
              AND v.resolved IS NOT NULL
            """
        )
    )


def downgrade() -> None:
    op.drop_table("terminal_bench_validations")
    op.drop_table("swe_explorer_validations")
    op.drop_table("swe_bench_verified_validations")
