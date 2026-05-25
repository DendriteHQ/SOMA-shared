"""add swebench orchestration state

Revision ID: 5b8d7e6a9c1f
Revises: 4c6d8e1f2a3b
Create Date: 2026-05-21

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "5b8d7e6a9c1f"
down_revision = "4c6d8e1f2a3b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "swe_bench_runs",
        sa.Column(
            "status",
            sa.String(length=32),
            nullable=False,
            server_default="pending",
        ),
    )
    op.add_column(
        "swe_bench_runs",
        sa.Column("last_error", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_swe_bench_runs_status",
        "swe_bench_runs",
        ["status"],
    )

    op.alter_column(
        "swe_bench_run_validations",
        "validator_fk",
        existing_type=sa.BigInteger(),
        nullable=True,
    )
    op.add_column(
        "swe_bench_run_validations",
        sa.Column("logs", sa.Text(), nullable=True),
    )
    op.add_column(
        "swe_bench_run_validations",
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "swe_bench_run_validations",
        sa.Column("claim_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_swe_bench_run_validations_scored_claim_expires",
        "swe_bench_run_validations",
        ["scored_at", "claim_expires_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_swe_bench_run_validations_scored_claim_expires",
        table_name="swe_bench_run_validations",
    )
    op.drop_column("swe_bench_run_validations", "claim_expires_at")
    op.drop_column("swe_bench_run_validations", "claimed_at")
    op.drop_column("swe_bench_run_validations", "logs")
    op.alter_column(
        "swe_bench_run_validations",
        "validator_fk",
        existing_type=sa.BigInteger(),
        nullable=False,
    )

    op.drop_index(
        "ix_swe_bench_runs_status",
        table_name="swe_bench_runs",
    )
    op.drop_column("swe_bench_runs", "last_error")
    op.drop_column("swe_bench_runs", "status")
