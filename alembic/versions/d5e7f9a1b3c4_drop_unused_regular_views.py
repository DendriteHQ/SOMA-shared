"""Drop unused regular views before rebuild.

Revision ID: d5e7f9a1b3c4
Revises: 3d2be0724e0c
Create Date: 2026-04-20
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from soma_shared.db.views.v_competition_challenges import v_competition_challenges
from soma_shared.db.views.v_miner_competition_ratio_ranked import v_miner_competition_ratio_ranked
from soma_shared.db.views.v_miner_competition_stats import v_miner_competition_stats
from soma_shared.db.views.v_miner_screener_stats import v_miner_screener_stats


revision = "d5e7f9a1b3c4"
down_revision = "3d2be0724e0c"
branch_labels = None
depends_on = None


def _compile(selectable: sa.sql.Select) -> str:
    return str(
        selectable.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


def upgrade() -> None:
    op.execute(sa.text("DROP VIEW IF EXISTS v_miner_competition_ratio_ranked CASCADE"))
    op.execute(sa.text("DROP VIEW IF EXISTS v_miner_competition_stats CASCADE"))
    op.execute(sa.text("DROP VIEW IF EXISTS v_miner_screener_stats CASCADE"))
    op.execute(sa.text("DROP VIEW IF EXISTS v_competition_challenges CASCADE"))


def downgrade() -> None:
    for view_def in (
        v_competition_challenges(),
        v_miner_screener_stats(),
        v_miner_competition_stats(),
        v_miner_competition_ratio_ranked(),
    ):
        sql = _compile(view_def.selectable)
        op.execute(sa.text(f"CREATE VIEW {view_def.name} AS {sql}"))