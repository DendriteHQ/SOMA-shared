"""add unique index on normalized competition name

Revision ID: d8f1a3c5e7b9
Revises: c5a7e9b1d3f2
Create Date: 2026-10-22

Miners select a competition by name on /miner/run-logs, so a name must identify a
single competition. Uniqueness ignores case and surrounding whitespace, the same
normalization the lookup uses. The upgrade fails if duplicates already exist; find
them with:

    SELECT lower(btrim(competition_name)), array_agg(id)
    FROM competitions GROUP BY 1 HAVING count(*) > 1;
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "d8f1a3c5e7b9"
down_revision = "c5a7e9b1d3f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "uq_competitions_competition_name_normalized",
        "competitions",
        [sa.text("lower(btrim(competition_name))")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_competitions_competition_name_normalized", table_name="competitions")
