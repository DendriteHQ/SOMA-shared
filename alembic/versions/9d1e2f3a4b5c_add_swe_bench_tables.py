"""add swe bench tables

Revision ID: 9d1e2f3a4b5c
Revises: b2d4f6a8c0e1
Create Date: 2026-05-20

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "9d1e2f3a4b5c"
down_revision = "b2d4f6a8c0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "swe_bench_tasks",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("competition_fk", sa.BigInteger(), nullable=False),
        sa.Column("instance_id", sa.String(length=255), nullable=False),
        sa.Column("planned_repeats", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_screener", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.ForeignKeyConstraint(
            ["competition_fk"],
            ["competitions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "swe_bench_runs",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("task_fk", sa.BigInteger(), nullable=False),
        sa.Column("request_fk", sa.BigInteger(), nullable=True),
        sa.Column("attempt_no", sa.Integer(), nullable=False),
        sa.Column("miner_fk", sa.BigInteger(), nullable=True),
        sa.Column("script_fk", sa.BigInteger(), nullable=True),
        sa.Column("diff_storage_uuid", sa.Text(), nullable=False),
        sa.Column("tokens_used", sa.BigInteger(), nullable=True),
        sa.Column("time_taken_seconds", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("agent_steps", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("baseline_run", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["task_fk"],
            ["swe_bench_tasks.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["request_fk"],
            ["requests.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["miner_fk"], ["miners.id"]),
        sa.ForeignKeyConstraint(["script_fk"], ["scripts.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("diff_storage_uuid"),
    )

    op.create_table(
        "swe_bench_run_validations",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("run_fk", sa.BigInteger(), nullable=False),
        sa.Column("request_fk", sa.BigInteger(), nullable=True),
        sa.Column("validator_fk", sa.BigInteger(), nullable=False),
        sa.Column("resolved", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scored_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["run_fk"],
            ["swe_bench_runs.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["request_fk"],
            ["requests.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(["validator_fk"], ["validators.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("swe_bench_run_validations")
    op.drop_table("swe_bench_runs")
    op.drop_table("swe_bench_tasks")
