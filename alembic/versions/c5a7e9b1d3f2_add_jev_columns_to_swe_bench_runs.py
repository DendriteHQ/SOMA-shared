"""add jev columns to swe_bench_runs

Revision ID: c5a7e9b1d3f2
Revises: b7e2c4a9f0d1
Create Date: 2026-10-01

Compressor services: a miner's compressor may call Jev (the TypeSafe decision
model) through the benchmark proxy. What that cost is recorded per run, apart
from the agent's own LLM tokens:

    jev_calls         number of Jev calls
    jev_input_tokens  Jev input tokens (Jev bills input only)
    jev_cost_usd      cost reported by OpenRouter

The score counts jev_input_tokens on the miner side with its own weight; baseline
runs have no compressor and leave them NULL. All nullable with no backfill: a run
recorded before this column existed made no Jev calls.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "c5a7e9b1d3f2"
down_revision = "b7e2c4a9f0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("swe_bench_runs", sa.Column("jev_calls", sa.Integer(), nullable=True))
    op.add_column("swe_bench_runs", sa.Column("jev_input_tokens", sa.BigInteger(), nullable=True))
    op.add_column("swe_bench_runs", sa.Column("jev_cost_usd", sa.Numeric(14, 8), nullable=True))


def downgrade() -> None:
    op.drop_column("swe_bench_runs", "jev_cost_usd")
    op.drop_column("swe_bench_runs", "jev_input_tokens")
    op.drop_column("swe_bench_runs", "jev_calls")
