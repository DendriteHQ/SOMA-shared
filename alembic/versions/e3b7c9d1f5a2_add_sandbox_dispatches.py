"""add sandbox_dispatches journal

Revision ID: e3b7c9d1f5a2
Revises: b6b6ade20fc1
Create Date: 2026-11-10

One row per attempt to hand a SWE-bench run to a sandbox, written by the run
coordinator and completed by the sandbox's result callback. It has no foreign keys:
the auto-run-restarter deletes failed runs, and the journal must keep counting the
sandbox work behind them.

A fresh database already gets this table from Base.metadata.create_all, so every
operation here is a no-op when the table and its indexes exist.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "e3b7c9d1f5a2"
down_revision = "b6b6ade20fc1"
branch_labels = None
depends_on = None


_INDEXES = (
    ("ix_sandbox_dispatches_sandbox_id_dispatched_at", ["sandbox_id", "dispatched_at"]),
    ("ix_sandbox_dispatches_sandbox_url_dispatched_at", ["sandbox_url", "dispatched_at"]),
    ("ix_sandbox_dispatches_run_id", ["run_id"]),
    ("ix_sandbox_dispatches_competition_fk_instance_id", ["competition_fk", "instance_id"]),
    ("ix_sandbox_dispatches_dispatched_at", ["dispatched_at"]),
)


def upgrade() -> None:
    op.create_table(
        "sandbox_dispatches",
        sa.Column("dispatch_id", sa.Text(), primary_key=True),
        sa.Column("run_id", sa.BigInteger(), nullable=False),
        sa.Column("sandbox_url", sa.Text(), nullable=True),
        sa.Column("sandbox_id", sa.Text(), nullable=True),
        sa.Column("attempt_index", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("competition_fk", sa.BigInteger(), nullable=True),
        sa.Column("instance_id", sa.String(length=255), nullable=True),
        sa.Column("miner_fk", sa.BigInteger(), nullable=True),
        sa.Column("benchmark_type", sa.String(length=64), nullable=True),
        sa.Column("baseline_run", sa.Boolean(), nullable=True),
        sa.Column(
            "dispatched_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("dispatch_outcome", sa.String(length=32), nullable=False),
        sa.Column("dispatch_http_status", sa.Integer(), nullable=True),
        sa.Column("dispatch_error", sa.Text(), nullable=True),
        sa.Column("reported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("report_ok", sa.Boolean(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("error_class", sa.String(length=64), nullable=True),
        sa.Column("execution_time_seconds", sa.Numeric(10, 4), nullable=True),
        sa.Column("agent_steps", sa.Integer(), nullable=True),
        sa.Column("tokens_used", sa.BigInteger(), nullable=True),
        sa.Column("report_applied", sa.Boolean(), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_reason", sa.String(length=32), nullable=True),
        sa.CheckConstraint(
            "dispatch_outcome IN ('accepted', 'rejected', 'error', 'ack_timeout')",
            name="ck_sandbox_dispatches_dispatch_outcome",
        ),
        sa.CheckConstraint(
            "closed_reason IS NULL OR closed_reason IN ('reported', 'ttl_expired')",
            name="ck_sandbox_dispatches_closed_reason",
        ),
        if_not_exists=True,
    )
    for name, columns in _INDEXES:
        op.create_index(name, "sandbox_dispatches", columns, if_not_exists=True)


def downgrade() -> None:
    for name, _ in reversed(_INDEXES):
        op.drop_index(name, table_name="sandbox_dispatches", if_exists=True)
    op.drop_table("sandbox_dispatches", if_exists=True)
