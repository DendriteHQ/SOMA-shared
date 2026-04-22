"""Add supporting indexes for heavy view workloads.

Revision ID: d4e6f8a1b2c3
Revises: d5e7f9a1b3c4
Create Date: 2026-04-20
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "d4e6f8a1b2c3"
down_revision = "d5e7f9a1b3c4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_challenge_batches_script_fk",
        "challenge_batches",
        ["script_fk"],
    )

    op.create_index(
        "ix_miner_uploads_script_fk_competition_fk_created_at",
        "miner_uploads",
        ["script_fk", "competition_fk", "created_at"],
    )

    op.create_index(
        "ix_batch_challenges_challenge_fk_challenge_batch_fk",
        "batch_challenges",
        ["challenge_fk", "challenge_batch_fk"],
    )

    op.create_index(
        "ix_competition_challenges_active_competition_fk_challenge_fk",
        "competition_challenges",
        ["competition_fk", "challenge_fk"],
        postgresql_where=sa.text("is_active = true"),
    )

    op.create_index(
        "ix_competition_challenges_active_challenge_fk_competition_fk",
        "competition_challenges",
        ["challenge_fk", "competition_fk"],
        postgresql_where=sa.text("is_active = true"),
    )

    op.create_index(
        "ix_screening_challenges_screener_fk_challenge_fk",
        "screening_challenges",
        ["screener_fk", "challenge_fk"],
    )

    op.create_index(
        "ix_screening_challenges_challenge_fk_screener_fk",
        "screening_challenges",
        ["challenge_fk", "screener_fk"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_screening_challenges_challenge_fk_screener_fk",
        table_name="screening_challenges",
    )
    op.drop_index(
        "ix_screening_challenges_screener_fk_challenge_fk",
        table_name="screening_challenges",
    )
    op.drop_index(
        "ix_competition_challenges_active_challenge_fk_competition_fk",
        table_name="competition_challenges",
    )
    op.drop_index(
        "ix_competition_challenges_active_competition_fk_challenge_fk",
        table_name="competition_challenges",
    )
    op.drop_index(
        "ix_batch_challenges_challenge_fk_challenge_batch_fk",
        table_name="batch_challenges",
    )
    op.drop_index(
        "ix_miner_uploads_script_fk_competition_fk_created_at",
        table_name="miner_uploads",
    )
    op.drop_index(
        "ix_challenge_batches_script_fk",
        table_name="challenge_batches",
    )