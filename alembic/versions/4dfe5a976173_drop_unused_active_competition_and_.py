"""Drop all now-unused v_*/mv_* views.

Merges the two divergent heads. None of these views are read by application
code anymore: mcp_platform now queries the underlying tables directly, the
mv_* refresh task was already removed, and fetch_top_screener_miner_ids_for_competition
(the last reader of v_miner_screener_eligible_ranked) was removed along with
its only caller, _select_miner_ss58.

Revision ID: 4dfe5a976173
Revises: a4d6f8b2c0e3, c7d9e1f3a5b8
Create Date: 2026-07-27
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from soma_shared.db.views.v_active_competition import v_active_competition
from soma_shared.db.views.v_competition_challenges import v_competition_challenges
from soma_shared.db.views.v_miner_competition_stats import v_miner_competition_stats
from soma_shared.db.views.v_miner_screener_eligible_ranked import v_miner_screener_eligible_ranked
from soma_shared.db.views.v_miner_screener_stats import v_miner_screener_stats
from soma_shared.db.views.v_miner_status import v_miner_status


revision = "4dfe5a976173"
down_revision = ("a4d6f8b2c0e3", "c7d9e1f3a5b8")
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
    op.execute(sa.text("DROP MATERIALIZED VIEW IF EXISTS mv_competition_challenges CASCADE"))
    op.execute(sa.text("DROP MATERIALIZED VIEW IF EXISTS mv_miner_screener_stats CASCADE"))
    op.execute(sa.text("DROP MATERIALIZED VIEW IF EXISTS mv_miner_status CASCADE"))
    op.execute(sa.text("DROP MATERIALIZED VIEW IF EXISTS mv_miner_competition_stats CASCADE"))
    op.execute(sa.text("DROP VIEW IF EXISTS v_active_competition CASCADE"))
    op.execute(sa.text("DROP VIEW IF EXISTS v_miner_status CASCADE"))
    op.execute(sa.text("DROP VIEW IF EXISTS v_miner_screener_eligible_ranked CASCADE"))


def downgrade() -> None:
    for view_def in (v_active_competition(), v_miner_status(), v_miner_screener_eligible_ranked()):
        sql = _compile(view_def.selectable)
        op.execute(sa.text(f"CREATE VIEW {view_def.name} AS {sql}"))

    for mv in (
        v_competition_challenges(materialized=True, unique_index_columns=("competition_id", "challenge_id")),
        v_miner_screener_stats(materialized=True, unique_index_columns=("competition_id", "ss58")),
        v_miner_status(materialized=True, unique_index_columns=("competition_id", "ss58")),
        v_miner_competition_stats(materialized=True, unique_index_columns=("competition_id", "ss58")),
    ):
        sql = _compile(mv.selectable)
        op.execute(sa.text(f"CREATE MATERIALIZED VIEW {mv.name} AS {sql}"))
        if mv.unique_index_columns:
            idx = f"{mv.name}_uidx"
            cols = ", ".join(mv.unique_index_columns)
            op.execute(sa.text(f"CREATE UNIQUE INDEX IF NOT EXISTS {idx} ON {mv.name} ({cols})"))
