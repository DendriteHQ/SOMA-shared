"""Add supporting indexes for live-view query hot paths.

Revision ID: f9a1b2c3d4e5
Revises: e6f7a8b9c0d1
Create Date: 2026-04-29
"""

from __future__ import annotations

from alembic import op


revision = "f9a1b2c3d4e5"
down_revision = "e6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Speeds EXISTS/anti-join checks keyed by challenge_batches.miner_fk.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_challenge_batches_miner_fk
        ON challenge_batches (miner_fk)
        """
    )

    # Makes competition-filtered upload scans index-friendly.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_miner_uploads_competition_fk_script_fk_created_at
        ON miner_uploads (competition_fk, script_fk, created_at)
        """
    )

    # Supports joins from scripts to miners in view expansion plans.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_scripts_miner_fk
        ON scripts (miner_fk)
        """
    )

    # Helps score lookups used by screener score aggregations.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_batch_challenge_scores_batch_challenge_fk_score
        ON batch_challenge_scores (batch_challenge_fk, score)
        """
    )


def downgrade() -> None:
    op.execute(
        "DROP INDEX IF EXISTS ix_batch_challenge_scores_batch_challenge_fk_score"
    )
    op.execute(
        "DROP INDEX IF EXISTS ix_scripts_miner_fk"
    )
    op.execute(
        "DROP INDEX IF EXISTS ix_miner_uploads_competition_fk_script_fk_created_at"
    )
    op.execute(
        "DROP INDEX IF EXISTS ix_challenge_batches_miner_fk"
    )

