"""Redesign top_miners for overall and per-category winners.

Revision ID: f7b3c2a1d9e4
Revises: e4b9c1d2a6f7
Create Date: 2026-04-02

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "f7b3c2a1d9e4"
down_revision = "e4b9c1d2a6f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "top_miners",
        sa.Column("competition_fk", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "top_miners",
        sa.Column(
            "winner_type",
            sa.String(length=32),
            nullable=False,
            server_default="overall",
        ),
    )
    op.add_column(
        "top_miners",
        sa.Column("compression_ratio", sa.Float(), nullable=True),
    )

    op.create_foreign_key(
        "fk_top_miners_competition",
        "top_miners",
        "competitions",
        ["competition_fk"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_check_constraint(
        "chk_top_miner_winner_type",
        "top_miners",
        "winner_type IN ('overall', 'compression_ratio')",
    )
    op.create_check_constraint(
        "chk_top_miner_category_shape",
        "top_miners",
        "("
        "(winner_type = 'overall' AND compression_ratio IS NULL) "
        "OR "
        "(winner_type = 'compression_ratio' AND compression_ratio IS NOT NULL)"
        ")",
    )

    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_top_miners_competition_fk "
            "ON top_miners (competition_fk)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_top_miners_winner_type "
            "ON top_miners (winner_type)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_top_miners_compression_ratio "
            "ON top_miners (compression_ratio)"
        )
    )
    op.execute(
        sa.text(
            "CREATE INDEX IF NOT EXISTS ix_top_miners_winner_lookup "
            "ON top_miners (competition_fk, winner_type, compression_ratio, starts_at, ends_at, created_at)"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP INDEX IF EXISTS ix_top_miners_winner_lookup"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_top_miners_compression_ratio"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_top_miners_winner_type"))
    op.execute(sa.text("DROP INDEX IF EXISTS ix_top_miners_competition_fk"))

    op.drop_constraint("chk_top_miner_category_shape", "top_miners", type_="check")
    op.drop_constraint("chk_top_miner_winner_type", "top_miners", type_="check")
    op.drop_constraint("fk_top_miners_competition", "top_miners", type_="foreignkey")

    op.drop_column("top_miners", "compression_ratio")
    op.drop_column("top_miners", "winner_type")
    op.drop_column("top_miners", "competition_fk")

