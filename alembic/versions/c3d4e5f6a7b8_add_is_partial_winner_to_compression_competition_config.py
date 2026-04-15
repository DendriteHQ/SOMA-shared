"""Add is_partial_winner to compression_competition_config.

Revision ID: c3d4e5f6a7b8
Revises: b1c2d3e4f5a6
Create Date: 2026-04-15

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "c3d4e5f6a7b8"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "compression_competition_config",
        sa.Column(
            "is_partial_winner",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    # Remove server default after backfill so future inserts must be explicit
    op.alter_column(
        "compression_competition_config",
        "is_partial_winner",
        server_default=None,
    )

    # Set is_partial_winner=true for Context-Compression-4 and Context-Compression-5
    op.execute(
        sa.text(
            """
            UPDATE compression_competition_config ccc
            SET is_partial_winner = true
            FROM competition_configs cc
            JOIN competitions c ON c.id = cc.competition_fk
            WHERE ccc.competition_config_fk = cc.id
              AND c.competition_name IN ('Context-Compression-4', 'Context-Compression-5')
            """
        )
    )


def downgrade() -> None:
    op.drop_column("compression_competition_config", "is_partial_winner")
