"""add swe_bench_verified_validations and swe_explorer_validations tables

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
        sa.Column("resolved", sa.Boolean(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["validation_fk"],
            ["swe_bench_run_validations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("validation_fk"),
    )

    op.create_table(
        "swe_explorer_edit_validations",
        sa.Column("validation_fk", sa.BigInteger(), nullable=False),
        sa.Column("resolved", sa.Boolean(), nullable=False),
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
        sa.Column("precision", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("recall", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("f1_score", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("hit_file_rate", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("noise_file_rate", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("weighted_core_coverage", sa.Numeric(precision=10, scale=6), nullable=True),
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
            INSERT INTO swe_bench_verified_validations (validation_fk, resolved, details)
            SELECT
                v.id AS validation_fk,
                COALESCE(v.resolved, FALSE) AS resolved,
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
    op.drop_table("swe_explorer_validations")
    op.drop_table("swe_explorer_edit_validations")
    op.drop_table("swe_bench_verified_validations")
